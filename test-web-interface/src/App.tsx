import React, { useState } from 'react';
import './App.css';

type ReportLength = 'simple' | 'moderate' | 'detailed';

interface AnalysisResult {
  success: boolean;
  content?: string;
  error?: string;
  details?: string[];
  metadata?: {
    charCount: number;
    processingTime: number;
    timestamp: string;
    reportFile?: string;
    searchKeywords?: string;
  };
  htmlReport?: string;
}

const App: React.FC = () => {
  const [userInput, setUserInput] = useState<string>('');
  const [reportLength, setReportLength] = useState<ReportLength>('moderate');
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [result, setResult] = useState<AnalysisResult | null>(null);

  // 글자수 계산 (기본 1200자 기준)
  const getTargetCharCount = (length: ReportLength): number => {
    const baseCount = 1200;
    switch (length) {
      case 'simple': return baseCount;
      case 'moderate': return Math.floor(baseCount * 1.5);
      case 'detailed': return baseCount * 2;
      default: return baseCount;
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!userInput.trim()) {
      alert('분석할 내용을 입력해주세요.');
      return;
    }

    setIsLoading(true);
    setResult(null);

    const startTime = Date.now();
    const targetCharCount = getTargetCharCount(reportLength);

    try {
      // 백엔드 API 호출
      const response = await simulateGPTAnalysis(userInput, targetCharCount, reportLength);
      
      const processingTime = Date.now() - startTime;
      
      setResult({
        success: true,
        content: response.content,
        metadata: response.metadata || {
          charCount: response.content.length,
          processingTime,
          timestamp: new Date().toLocaleString('ko-KR')
        },
        htmlReport: response.htmlReport
      });
    } catch (error: any) {
      setResult({
        success: false,
        error: error instanceof Error ? error.message : '알 수 없는 오류가 발생했습니다.',
        details: error.details
      });
    } finally {
      setIsLoading(false);
    }
  };

  // 실제 GPT API 호출 함수
  const simulateGPTAnalysis = async (
    input: string, 
    targetCharCount: number, 
    length: ReportLength
  ): Promise<any> => {
    const response = await fetch('http://localhost:3001/api/analyze', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        userInput: input,
        reportLength: length
      })
    });

    if (!response.ok) {
      const errorData = await response.json();
      // details가 있으면 함께 전달
      const error: any = new Error(errorData.error || '서버 오류가 발생했습니다.');
      if (errorData.details) {
        error.details = errorData.details;
      }
      throw error;
    }

    const data = await response.json();
    
    if (!data.success) {
      const error: any = new Error(data.error || '분석에 실패했습니다.');
      if (data.details) {
        error.details = data.details;
      }
      throw error;
    }

    // 성공한 경우 전체 데이터 반환
    return data;
  };

  const resetForm = () => {
    setUserInput('');
    setResult(null);
    setReportLength('moderate');
  };

  return (
    <div className="App">
      <header className="app-header">
        <h1>🔍 Reddit 실시간 정보 수집 및 분석</h1>
        <p>Reddit에서 최신 정보를 수집하고 GPT-4로 분석합니다</p>
      </header>

      <main className="main-content">
        <form onSubmit={handleSubmit} className="analysis-form">
          <div className="form-group">
            <label htmlFor="userInput">
              <strong>검색할 키워드 입력:</strong>
            </label>
            <textarea
              id="userInput"
              value={userInput}
              onChange={(e) => setUserInput(e.target.value)}
              placeholder="예시: Tesla 2025 news, Python programming, AI technology&#10;여러 키워드는 쉼표(,)로 구분하세요"
              rows={4}
              className="input-textarea"
              disabled={isLoading}
            />
            <div className="char-count">
              {userInput.length} / 500자
            </div>
          </div>

          <div className="form-group">
            <label>
              <strong>보고서 길이 선택:</strong>
            </label>
            <div className="radio-group">
              <label className="radio-option">
                <input
                  type="radio"
                  value="simple"
                  checked={reportLength === 'simple'}
                  onChange={(e) => setReportLength(e.target.value as ReportLength)}
                  disabled={isLoading}
                />
                <span className="radio-label">
                  간단히 ({getTargetCharCount('simple')}자 목표)
                </span>
              </label>
              
              <label className="radio-option">
                <input
                  type="radio"
                  value="moderate"
                  checked={reportLength === 'moderate'}
                  onChange={(e) => setReportLength(e.target.value as ReportLength)}
                  disabled={isLoading}
                />
                <span className="radio-label">
                  적당히 ({getTargetCharCount('moderate')}자 목표)
                </span>
              </label>
              
              <label className="radio-option">
                <input
                  type="radio"
                  value="detailed"
                  checked={reportLength === 'detailed'}
                  onChange={(e) => setReportLength(e.target.value as ReportLength)}
                  disabled={isLoading}
                />
                <span className="radio-label">
                  상세하게 ({getTargetCharCount('detailed')}자 목표)
                </span>
              </label>
            </div>
          </div>

          <div className="button-group">
            <button 
              type="submit" 
              className="collect-button"
              disabled={isLoading || !userInput.trim()}
            >
              {isLoading ? '🔄 분석 중...' : '🚀 수집 & 분석'}
            </button>
            
            <button 
              type="button" 
              onClick={resetForm}
              className="reset-button"
              disabled={isLoading}
            >
              🔄 초기화
            </button>
          </div>
        </form>

        {isLoading && (
          <div className="loading-section">
            <div className="loading-spinner"></div>
            <p>Reddit에서 정보를 수집하고 있습니다...</p>
            <div className="loading-steps">
              <div className="step">🔍 Reddit 검색 중</div>
              <div className="step">📊 데이터 수집 중</div>
              <div className="step">🤖 GPT-4 분석 중</div>
              <div className="step">📝 보고서 생성 중</div>
            </div>
          </div>
        )}

        {result && (
          <div className={`result-section ${result.success ? 'success' : 'error'}`}>
            {result.success ? (
              <>
                <div className="result-header">
                  <h2>✅ 분석 완료</h2>
                  {result.metadata && (
                    <div className="metadata">
                      <span>📊 {result.metadata.charCount}자</span>
                      <span>⏱️ {(result.metadata.processingTime / 1000).toFixed(1)}초</span>
                      <span>🕐 {result.metadata.timestamp}</span>
                      {result.metadata.reportFile && (
                        <span>📄 {result.metadata.reportFile}</span>
                      )}
                    </div>
                  )}
                </div>
                
                <div className="result-content">
                  <pre>{result.content}</pre>
                </div>
                
                {result.htmlReport && (
                  <div className="html-report-section">
                    <h3>📊 상세 분석 보고서</h3>
                    <button 
                      onClick={() => {
                        const newWindow = window.open('', '_blank');
                        if (newWindow && result.htmlReport) {
                          newWindow.document.write(result.htmlReport);
                          newWindow.document.close();
                        }
                      }}
                      className="view-report-button"
                    >
                      🔍 HTML 보고서 보기
                    </button>
                  </div>
                )}
                
                <div className="result-actions">
                  <button 
                    onClick={() => navigator.clipboard.writeText(result.content || '')}
                    className="copy-button"
                  >
                    📋 복사
                  </button>
                  <button 
                    onClick={() => {
                      const blob = new Blob([result.content || ''], { type: 'text/plain' });
                      const url = URL.createObjectURL(blob);
                      const a = document.createElement('a');
                      a.href = url;
                      a.download = `analysis_${Date.now()}.txt`;
                      a.click();
                    }}
                    className="download-button"
                  >
                    💾 다운로드
                  </button>
                </div>
              </>
            ) : (
              <div className="error-content">
                <h2>❌ 분석 실패</h2>
                <p>{result.error}</p>
                {result.details && (
                  <div style={{ marginTop: '15px', textAlign: 'left', background: '#f8f9fa', padding: '15px', borderRadius: '8px' }}>
                    <strong>상세 오류:</strong>
                    <ul style={{ marginTop: '10px', paddingLeft: '20px' }}>
                      {result.details.map((detail, idx) => (
                        <li key={idx} style={{ color: '#e74c3c', marginBottom: '5px' }}>{detail}</li>
                      ))}
                    </ul>
                  </div>
                )}
                <button onClick={resetForm} className="retry-button">
                  🔄 다시 시도
                </button>
              </div>
            )}
          </div>
        )}
      </main>

      <footer className="app-footer">
        <p>Reddit Community Info Collector - 실시간 정보 수집 및 분석</p>
        <p>Reddit API + GPT-4 Turbo Preview</p>
      </footer>
    </div>
  );
};

export default App;