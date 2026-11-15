# mem-shape

`~/.mem`의 후보 모양 셋을 실제 폴더로 만들고, 네 단계(load, save, decision, split)의 파일을 차례로 얹어 세션이 받는 파일을 `ls`로 보이는 스크립트다. issue [기준에 비춰 `~/.mem` 모양과 그 이름을 어떻게 두는가](https://github.com/uwonu606/agent-memory-layer/issues/7)의 답이 이 출력으로 후보를 견줬다.

## 돌리기

```bash
bash lab/mem-shape/mem-shape-prototype.sh <아직 없는 폴더 경로>
```

스크립트는 그 폴더를 새로 만들고, 후보마다 가짜 home을 그 안에 둔다. 이미 있는 폴더를 주면 멈춘다.

## 읽는 법

- 세션이 받는 파일은 hook이 아니라 전역부터 target layer까지 layer마다 `ls -A`로 뽑는다. 이름이나 확장자로 거르지 않는다.
- `layers`, `log.md`, `retired`, `.hook`, `~/.mem-hook`, `contexts`는 견주려고 붙인 임시 이름이다.
- `output.txt`는 스크립트를 한 번 돌린 출력이다.
