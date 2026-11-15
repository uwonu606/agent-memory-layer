# agent-memory-layer

코딩 에이전트의 기억을 markdown 파일로 두고, 세션을 연 작업 위치에 맞는 기억만 load하는 도구의 낱말이다.

## Language

**layer**:
기억 파일이 놓이는 폴더 하나다. layer는 다른 layer 안에 놓일 수 있다.
_Avoid_: 층

**전역**:
가장 바깥 layer다. 모든 세션이 받는다.

**layer tree**:
전역과 그 안에 놓인 layer 전부다.
_Avoid_: 저장소

**target layer**:
작업 위치에 맞는 layer 가운데 가장 안쪽 layer다.

**맥락**:
회사 일이나 오픈소스 기여처럼 저장소 여럿이 묶이는 일이다. 폴더를 부르는 말로는 쓰지 않는다.
