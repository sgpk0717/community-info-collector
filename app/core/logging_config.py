"""
로깅 설정 - 보기 좋은 포맷과 색상 지원
"""
import logging
import sys
from datetime import datetime

class ColoredFormatter(logging.Formatter):
    """색상이 지원되는 로그 포매터"""
    
    # ANSI 색상 코드
    COLORS = {
        'DEBUG': '\033[36m',      # Cyan
        'INFO': '\033[32m',       # Green  
        'WARNING': '\033[33m',    # Yellow
        'ERROR': '\033[31m',      # Red
        'CRITICAL': '\033[35m',   # Magenta
    }
    
    RESET = '\033[0m'
    BOLD = '\033[1m'
    
    def format(self, record):
        # 로그 레벨 색상
        levelname_color = self.COLORS.get(record.levelname, self.RESET)
        
        # 시간 포맷 (더 간결하게)
        time_str = datetime.fromtimestamp(record.created).strftime('%H:%M:%S')
        
        # 모듈 이름 축약
        module_parts = record.name.split('.')
        if len(module_parts) > 2:
            # app.services.reddit_service -> services.reddit
            module_name = f"{module_parts[-2]}.{module_parts[-1].replace('_service', '')}"
        else:
            module_name = record.name
        
        # 로그 레벨 고정 너비 (8자)
        level = record.levelname.ljust(8)
        
        # 포맷 구성
        if sys.stdout.isatty():  # 터미널인 경우 색상 사용
            formatted = (
                f"{self.BOLD}[{time_str}]{self.RESET} "
                f"{levelname_color}{level}{self.RESET} "
                f"{self.BOLD}{module_name:>25}{self.RESET} | "
                f"{record.getMessage()}"
            )
        else:  # 파일이나 파이프인 경우 색상 없이
            formatted = f"[{time_str}] {level} {module_name:>25} | {record.getMessage()}"
        
        # 예외 정보가 있으면 추가
        if record.exc_info:
            formatted += '\n' + self.formatException(record.exc_info)
            
        return formatted

def setup_logging(level=logging.INFO):
    """로깅 설정 초기화"""
    
    # 루트 로거 설정
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    
    # 기존 핸들러 제거
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # 콘솔 핸들러 생성
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(ColoredFormatter())
    root_logger.addHandler(console_handler)
    
    # 특정 로거 레벨 조정 (너무 많은 로그 방지)
    logging.getLogger('httpx').setLevel(logging.WARNING)
    logging.getLogger('httpcore').setLevel(logging.WARNING)
    logging.getLogger('hpack').setLevel(logging.WARNING)
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('apscheduler').setLevel(logging.INFO)
    
    # 스케줄러 관련 로거는 더 자세히
    logging.getLogger('app.services.supabase_scheduler_service').setLevel(logging.DEBUG)
    logging.getLogger('app.services.supabase_schedule_service').setLevel(logging.DEBUG)
    
    return root_logger

# 스케줄러 전용 로거
def get_scheduler_logger():
    """스케줄러 전용 로거 생성"""
    logger = logging.getLogger('scheduler')
    
    # 이미 설정되어 있으면 반환
    if logger.handlers:
        return logger
        
    logger.setLevel(logging.DEBUG)
    logger.propagate = False
    
    # 스케줄러 전용 포매터
    formatter = logging.Formatter(
        '[%(asctime)s] %(levelname)-8s [SCHEDULER] %(message)s',
        datefmt='%H:%M:%S'
    )
    
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    
    return logger