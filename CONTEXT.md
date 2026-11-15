# agent-memory-layer

코딩 에이전트의 기억을 markdown 파일로 두고, 작업 위치에 맞는 기억만 load하는 도구의 낱말이다.

## Language

**layer**:
기억 파일이 놓이는 폴더 하나다. layer는 다른 layer 안에 놓일 수 있다.
_Avoid_: 층

**전역**:
가장 바깥 layer다. 모든 작업 위치에 맞아서 모든 세션이 받는다.

**layer tree**:
전역과 그 안에 놓인 layer 전부다.
_Avoid_: 저장소

**작업 위치**:
세션을 연 폴더다. 세션 도중 에이전트가 다른 폴더로 옮겨도 바뀌지 않는다.

**layer 규칙**:
작업 위치를 layer에 잇는 규칙이다. layer 규칙이 layer에 이은 경로가 작업 위치를 품으면 그 layer는 작업 위치에 맞는다.
_Avoid_: 맥락 규칙

**target layer**:
작업 위치에 맞는 layer 가운데 가장 안쪽 layer다. 전역보다 좁은 layer가 맞지 않으면 전역이다.

**맥락**:
회사 일이나 오픈소스 기여처럼 저장소 여럿이 묶이는 일이다. 폴더를 부르는 말로는 쓰지 않는다.
