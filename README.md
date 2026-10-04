# 七世紀歐亞地圖

黑白歐亞地圖：陸地白、水域淺灰，無國界、無文字。標出喜瑪拉雅山脈，以及七世紀六個政權的首都：君士坦丁堡（拜占庭）、長安（唐）、飛鳥（日本）、金城（新羅）、邏些（吐蕃）、麥地那（阿拉伯）。

## 使用

```sh
scripts/fetch-data.sh          # 下載來源資料到 data/
uv run scripts/prepare.py      # 產生 web/geo.js
```

用瀏覽器開啟 `web/index.html`，即可即時調整首都圖示、海岸線、山脈，再按「下載 SVG」匯出。設定存在瀏覽器裡，重新開啟時會保留。

`maps/eurasia-7th-century.svg` 是目前定稿的地圖，由 `scripts/build2.py` 產生；換成新版時把匯出的 SVG 覆蓋上去再 commit。

## 資料來源

- 底圖：Wikimedia Commons〈Afro-Eurasia location map with borders.svg〉，公有領域。等距圓柱投影，邊界取自 Wikipedia 的 Module:Location map/data/Afro-Eurasia（經度 −25.65～180、緯度 90～−48.15），首都依經緯度換算座標。
- 台灣：底圖的台灣只有幾個頂點，改用 Natural Earth 1:10m land，公有領域。
- 喜瑪拉雅山脈位置：Natural Earth 1:50m geography regions 的 HIMALAYAS 多邊形。

## 每個部分各有獨立的隨機種子

海岸線抖動、山峰排列、首都圖示的不規則形狀各用一個種子，調整其中一項不會讓其他部分跟著變動。
