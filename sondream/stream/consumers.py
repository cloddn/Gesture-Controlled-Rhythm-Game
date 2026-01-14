import json
import time
from channels.generic.websocket import AsyncWebsocketConsumer
# 작성하신 로직 파일을 같은 디렉토리에 두거나 import 가능한 경로에 두어야 합니다.
from .rhythm_game_logic import (
    PlayState, NoteEvent, NoteType, process_note_result, 
    TimingConfig, SpatialConfig, Judgement
)

class RhythmGameConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.accept()
        
        # 1. 게임 상태 초기화 (연결마다 별도의 상태 유지)
        self.state = PlayState()
        
        # 테스트를 위해 '목표 노트'를 하나 가상으로 생성해둡니다.
        self.set_next_test_target()
        
        await self.send(text_data=json.dumps({
            'type': 'system',
            'message': 'Game Connected. Note will appear in 2 seconds.',
            'target_start': self.current_test_note_start,
            'target_end': self.current_test_note_end
        }))

    async def disconnect(self, close_code):
        pass

    def set_next_test_target(self):
        """테스트용 다음 목표 설정"""
        self.current_test_note_start = time.time() * 1000 + 2000  # 2초 뒤
        self.current_test_note_end = self.current_test_note_start + 1000 # 1초 길이

    def calculate_final_rank(self):
        """
        [함수 분리] 게임 종료 시 최종 랭크 계산
        전체 누적 점수와 이론상 최대 점수를 비교하여 랭크 산정
        """
        if self.state.max_possible_score <= 0:
            return "F"
            
        ratio = self.state.total_score / self.state.max_possible_score
        
        if ratio >= 0.5: return "S"
        elif ratio >= 0.35: return "A"
        elif ratio >= 0.2: return "B"
        elif ratio >= 0.1: return "C"
        return "F"

    async def receive(self, text_data):
        data = json.loads(text_data)
        action = data.get('action')

        # [신규] 게임 종료 요청 처리
        if action == 'game_end':
            final_rank = self.calculate_final_rank()
            await self.send(text_data=json.dumps({
                'type': 'game_over',
                'total_score': round(self.state.total_score, 1),
                'max_possible_score': round(self.state.max_possible_score, 1),
                'rank': final_rank
            }))
            return

        # 클라이언트에서 손이 들어왔다 나간 이벤트(Gesture)를 보냈을 때
        if action == 'gesture_complete':
            actual_entry = data['entry_time'] # ms 단위 타임스탬프
            actual_exit = data['exit_time']   # ms 단위 타임스탬프
            min_dist = data.get('min_dist', 0) # 중심과의 거리

            # 2. 노트 이벤트 객체 생성
            note_event = NoteEvent(
                note_type=NoteType.TAP,
                target_start=self.current_test_note_start,
                target_end=self.current_test_note_end,
                target_x=100, target_y=100,
                actual_entry=actual_entry,
                actual_exit=actual_exit,
                min_dist=min_dist
            )

            # 3. 작성하신 로직(rhythm_game_logic.py) 실행
            # (여기서 반환되는 rank는 실시간 피드백용으로만 사용하거나 무시 가능)
            result = process_note_result(
                note=note_event,
                state=self.state,
                t_cfg=TimingConfig(), 
                s_cfg=SpatialConfig()
            )

            # 4. 결과 반환 (판정, 점수, 콤보 등)
            await self.send(text_data=json.dumps({
                'type': 'result',
                'data': result
            }))
            
            # 다음 테스트를 위해 목표 시간 갱신 (테스트용 루프)
            self.set_next_test_target()
            
            await self.send(text_data=json.dumps({
                'type': 'next_target',
                'target_start': self.current_test_note_start,
                'target_end': self.current_test_note_end
            }))