// Node.js용 Reddit 서비스 - axios 사용
const path = require('path');
const axios = require(path.join(__dirname, '../../test-web-interface/node_modules/axios'));

class RedditServiceNode {
  constructor() {
    this.clientId = process.env.REDDIT_CLIENT_ID;
    this.clientSecret = process.env.REDDIT_CLIENT_SECRET;
    this.userAgent = process.env.REDDIT_USER_AGENT || 'CommunityCollector/1.0';
    this.accessToken = null;
    this.tokenExpiry = 0;
  }

  async getAccessToken() {
    // 토큰이 유효하면 재사용
    if (this.accessToken && Date.now() < this.tokenExpiry) {
      return this.accessToken;
    }

    try {
      console.log('🔑 Reddit 액세스 토큰 요청 중...');
      
      const auth = Buffer.from(`${this.clientId}:${this.clientSecret}`).toString('base64');
      const response = await axios.post('https://www.reddit.com/api/v1/access_token', 
        'grant_type=client_credentials',
        {
          headers: {
            'Authorization': `Basic ${auth}`,
            'Content-Type': 'application/x-www-form-urlencoded',
            'User-Agent': this.userAgent
          }
        }
      );

      this.accessToken = response.data.access_token;
      // 토큰 만료 시간 설정 (보통 1시간)
      this.tokenExpiry = Date.now() + (response.data.expires_in * 1000) - 60000; // 1분 여유
      
      console.log('✅ Reddit 액세스 토큰 획득 성공');
      return this.accessToken;

    } catch (error) {
      console.error('❌ Reddit 토큰 획득 실패:', error.message);
      throw error;
    }
  }

  async searchPosts(query, options = {}) {
    const { limit = 25, sort = 'relevance' } = options;
    
    try {
      const token = await this.getAccessToken();
      
      console.log(`🔍 Reddit API 검색 중: "${query}" (정렬: ${sort}, 제한: ${limit})`);
      
      const response = await axios.get('https://oauth.reddit.com/search', {
        headers: {
          'Authorization': `Bearer ${token}`,
          'User-Agent': this.userAgent
        },
        params: {
          q: query,
          sort: sort,
          limit: limit,
          raw_json: 1
        }
      });

      const posts = response.data.data.children.map(child => {
        const post = child.data;
        return {
          post_id: post.id,
          title: post.title,
          author: post.author || '[deleted]',
          subreddit: post.subreddit,
          score: post.score,
          num_comments: post.num_comments,
          created_utc: post.created_utc,
          url: post.url,
          permalink: `https://reddit.com${post.permalink}`,
          selftext: post.selftext || '',
          is_self: post.is_self
        };
      });

      console.log(`✅ ${posts.length}개 Reddit 게시물 검색 완료`);
      return posts;

    } catch (error) {
      console.error('❌ Reddit API 검색 실패:', error.message);
      if (error.response) {
        console.error('응답 상태:', error.response.status);
        console.error('응답 데이터:', error.response.data);
      }
      throw new Error(`Reddit API 검색 실패: ${error.message}`);
    }
  }
}

module.exports = RedditServiceNode;