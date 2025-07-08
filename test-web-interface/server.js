const express = require('express');
const cors = require('cors');
const path = require('path');
const { spawn } = require('child_process');
const fs = require('fs').promises;
require('dotenv').config({ path: '../.env' });

const app = express();
const port = 3001;

// 미들웨어
app.use(cors());
app.use(express.json({ limit: '50mb' }));

// React 빌드 파일 서빙 (프로덕션용)
if (process.env.NODE_ENV === 'production') {
  app.use(express.static(path.join(__dirname, 'build')));
}

// Reddit 데이터 수집 및 분석 API
app.post('/api/analyze', async (req, res) => {
  console.log('\n==================================================');
  console.log('🚀 새로운 분석 요청 받음:', new Date().toLocaleString('ko-KR'));
  console.log('==================================================\n');
  
  try {
    const { userInput, reportLength } = req.body;
    console.log('📝 사용자 입력:', userInput);
    console.log('📏 보고서 길이:', reportLength);
    
    if (!userInput?.trim()) {
      console.log('❌ 오류: 입력값이 없음');
      return res.status(400).json({
        success: false,
        error: '검색할 키워드를 입력해주세요.'
      });
    }

    const startTime = Date.now();

    // 1단계: weighted_search.py 실행하여 데이터 수집
    console.log('🔍 [1단계] Reddit 데이터 수집 시작...');
    console.log('--------------------------------------------------');
    
    const searchScript = path.join(__dirname, '..', 'scripts', 'search', 'weighted_search.py');
    
    // 가상환경의 Python 경로 사용 (Windows/Linux 자동 감지)
    const isWindows = process.platform === 'win32';
    const pythonPath = isWindows 
      ? path.join(__dirname, '..', 'venv', 'Scripts', 'python.exe')
      : path.join(__dirname, '..', 'venv', 'bin', 'python');
    
    // 검색 키워드를 파이썬 스크립트에 전달
    const searchProcess = spawn(pythonPath, [searchScript, userInput], {
      env: { ...process.env }
    });

    let searchOutput = '';
    let searchError = '';

    searchProcess.stdout.on('data', (data) => {
      const output = data.toString();
      searchOutput += output;
      console.log(output);
    });

    searchProcess.stderr.on('data', (data) => {
      const error = data.toString();
      searchError += error;
      console.error('검색 오류:', error);
    });

    // 검색 완료 대기
    await new Promise((resolve, reject) => {
      searchProcess.on('close', (code) => {
        if (code !== 0) {
          reject(new Error(`검색 프로세스가 코드 ${code}로 종료됨`));
        } else {
          resolve();
        }
      });
    });

    console.log('\n✅ 데이터 수집 완료!');

    // 2단계: verified_analysis.py 실행하여 분석
    console.log('\n🤖 [2단계] GPT-4.1 분석 시작...');
    console.log('--------------------------------------------------');
    
    const analysisScript = path.join(__dirname, '..', 'scripts', 'analysis', 'verified_analysis.py');
    
    const analysisProcess = spawn(pythonPath, [analysisScript, userInput], {
      env: { ...process.env }
    });

    let analysisOutput = '';
    let analysisError = '';

    analysisProcess.stdout.on('data', (data) => {
      const output = data.toString();
      analysisOutput += output;
      console.log(output);
    });

    analysisProcess.stderr.on('data', (data) => {
      const error = data.toString();
      analysisError += error;
      console.error('분석 오류:', error);
    });

    // 분석 완료 대기
    await new Promise((resolve, reject) => {
      analysisProcess.on('close', (code) => {
        if (code !== 0) {
          reject(new Error(`분석 프로세스가 코드 ${code}로 종료됨`));
        } else {
          resolve();
        }
      });
    });

    // 생성된 HTML 파일 찾기
    const reportsDir = path.join(__dirname, '..', 'reports', 'ai_analysis');
    console.log('\n📂 보고서 디렉토리 확인:', reportsDir);
    
    const files = await fs.readdir(reportsDir);
    console.log('📁 전체 파일 목록:', files);
    
    const htmlFiles = files.filter(f => f.startsWith('verified_') && f.endsWith('.html'));
    console.log('📄 HTML 파일 목록:', htmlFiles);
    
    if (htmlFiles.length === 0) {
      console.log('❌ HTML 파일 없음');
      throw new Error('분석 보고서 파일을 찾을 수 없습니다');
    }

    // 가장 최신 파일 선택 (파일 수정 시간 기준)
    console.log('\n⏰ 파일 통계 수집 시작...');
    const filesWithStats = [];
    
    for (const file of htmlFiles) {
      try {
        const filePath = path.join(reportsDir, file);
        console.log(`📊 파일 통계 확인: ${file}`);
        console.log(`📂 전체 경로: ${filePath}`);
        
        const stats = await fs.stat(filePath);
        filesWithStats.push({ 
          file, 
          mtime: stats.mtime,
          size: stats.size 
        });
        
        console.log(`✅ 성공: ${file} (${stats.size} bytes, ${stats.mtime})`);
      } catch (error) {
        console.log(`❌ 파일 통계 가져오기 실패: ${file}`);
        console.log(`   오류 세부사항: ${error.message}`);
        console.log(`   오류 코드: ${error.code}`);
      }
    }
    
    console.log(`\n📋 유효한 파일 수: ${filesWithStats.length}/${htmlFiles.length}`);
    
    if (filesWithStats.length === 0) {
      console.log('❌ 유효한 파일 없음');
      throw new Error('유효한 분석 보고서 파일을 찾을 수 없습니다');
    }
    
    const sortedFiles = filesWithStats.sort((a, b) => b.mtime - a.mtime);
    const latestFile = sortedFiles[0].file;
    
    console.log('\n🏆 최신 파일 선택:');
    console.log(`   파일명: ${latestFile}`);
    console.log(`   수정시간: ${sortedFiles[0].mtime}`);
    console.log(`   크기: ${sortedFiles[0].size} bytes`);
    
    const htmlPath = path.join(reportsDir, latestFile);
    console.log(`📖 HTML 파일 읽기 시작: ${htmlPath}`);
    
    // HTML 파일 읽기
    const htmlContent = await fs.readFile(htmlPath, 'utf-8');
    console.log(`✅ HTML 파일 읽기 성공 (${htmlContent.length} 문자)`);
    
    // HTML에서 분석 내용 추출
    const contentMatch = htmlContent.match(/<div class="content">([\s\S]*?)<div class='footnotes'>/);
    const analysis = contentMatch ? contentMatch[1].replace(/<[^>]*>/g, '').trim() : '분석 내용을 추출할 수 없습니다';

    const processingTime = Date.now() - startTime;
    
    console.log('\n==================================================');
    console.log('✅ 분석 완료!');
    console.log(`⏱️  총 소요 시간: ${processingTime}ms`);
    console.log(`📄 보고서 파일: ${latestFile}`);
    console.log('==================================================\n');

    // 결과 반환
    res.json({
      success: true,
      content: analysis,
      metadata: {
        charCount: analysis.length,
        processingTime,
        timestamp: new Date().toLocaleString('ko-KR'),
        reportFile: latestFile,
        searchKeywords: userInput
      },
      htmlReport: htmlContent
    });

  } catch (error) {
    console.error('\n❌ 서버 오류:', error);
    res.status(500).json({
      success: false,
      error: '서버 오류가 발생했습니다: ' + error.message
    });
  }
});

// 상태 확인
app.get('/api/status', (req, res) => {
  console.log('📊 상태 확인 요청');
  const status = {
    status: 'OK',
    timestamp: new Date().toISOString(),
    openaiConfigured: !!process.env.OPENAI_API_KEY,
    redditConfigured: !!(process.env.REDDIT_CLIENT_ID && process.env.REDDIT_CLIENT_SECRET)
  };
  console.log('상태:', status);
  res.json(status);
});

// React 앱 서빙 (프로덕션)
if (process.env.NODE_ENV === 'production') {
  app.get('*', (req, res) => {
    res.sendFile(path.join(__dirname, 'build/index.html'));
  });
}

app.listen(port, () => {
  console.log('\n🚀 Reddit 분석 서버 시작!');
  console.log('==================================================');
  console.log(`📡 포트: ${port}`);
  console.log(`📊 상태: http://localhost:${port}/api/status`);
  console.log(`🔑 OpenAI API: ${process.env.OPENAI_API_KEY ? '✅ 설정됨' : '❌ 없음'}`);
  console.log(`🔑 Reddit API: ${process.env.REDDIT_CLIENT_ID ? '✅ 설정됨' : '❌ 없음'}`);
  console.log('==================================================\n');
});