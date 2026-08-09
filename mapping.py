import streamlit as st
import folium
from streamlit_folium import st_folium
import networkx as nx
import osmnx as ox
import pandas as pd

st.set_page_config(layout="wide") # 画面を広く使う
st.title("🚲 福島高専への自転車通学ルート比較アプリ")

# 1. 地点データの定義（中心となる目的地と、複数の出発地）
kosen_coord = (37.033577, 140.890804) # 福島高専

stations = {
    "いわき駅": (37.0583, 140.8923),
    "内郷駅": (37.0366, 140.8653),
    "湯本駅": (36.9946, 140.8492),
    "草野駅": (37.0874, 140.9178),
    "上荒川公園": (37.0330, 140.8976),
    "医療創生大学": (37.0188, 140.9169),
    "いわきエブリア": （36.9940, 140.9051),
    "アクアマリンふくしま": (36.9427, 140.9015),
    "塩屋崎灯台": (36.9919, 140.9853)
}

# 自転車の平均時速（所要時間計算用）
bike_speed_kmph = 15

# 2. 道路網データの取得（事前保存したファイルから読み込む）
@st.cache_resource
def load_bike_graph():
    # アップロードしたファイルから直接読み込む（API通信をしない）
    return ox.load_graphml("bike_graph.graphml")

with st.spinner("自転車用の道路網データを取得中..."):
    G = load_bike_graph()

# 高専の最寄りノードを取得
dest_node = ox.nearest_nodes(G, X=kosen_coord[1], Y=kosen_coord[0])

# 3. ルートと距離・時間の計算
results = []
routes_dict = {}

for station_name, coord in stations.items():
    # 各駅の最寄りノード
    orig_node = ox.nearest_nodes(G, X=coord[1], Y=coord[0])
    
    # 経路と距離の計算
    try:
        route = nx.shortest_path(G, orig_node, dest_node, weight='length')
        distance_m = nx.shortest_path_length(G, orig_node, dest_node, weight='length')
        distance_km = round(distance_m / 1000, 2) # kmに変換
        
        # 所要時間を計算（分）
        time_minutes = round((distance_km / bike_speed_kmph) * 60, 1)
        
        routes_dict[station_name] = route
        results.append({
            "地点名": station_name, 
            "距離 (km)": distance_km,
            "所要時間 (分)": time_minutes
        })
    except nx.NetworkXNoPath:
        st.warning(f"{station_name}からのルートが見つかりませんでした。")

# 結果をデータフレーム化して距離順に並べ替え
# 表示用の列名に変更
df_results = pd.DataFrame(results).sort_values("距離 (km)")

# 4. 画面レイアウト（左に表、右に地図）
col1, col2 = st.columns([1, 2])

with col1:
    st.subheader("📊 距離・時間の比較")
    st.dataframe(df_results, hide_index=True, use_container_width=True)
    st.info(f"※所要時間は平均時速{bike_speed_kmph}kmで計算した目安です。")

with col2:
    st.subheader("🗺️ ルートマップ")
    # 地図の初期化（高専を中心に）
    m = folium.Map(location=kosen_coord, zoom_start=13)
    
    # 高専のマーカー（星マーク）
    folium.Marker(
        kosen_coord, popup="福島高専", 
        icon=folium.Icon(color="red", icon="star")
    ).add_to(m)

    # 【1】色のリストを10色に拡張
    colors = [
        "blue", "green", "purple", "orange", "red", 
        "darkblue", "darkgreen", "darkpurple", "cadetblue", "pink"
    ]
    
    for i, (station_name, coord) in enumerate(stations.items()):
        color = colors[i % len(colors)]
        
        # 【3】場所の種類によってアイコンを変える
        if "駅" in station_name:
            icon_name = "info-sign" # 駅は情報
        elif "創生大学" in station_name:
            icon_name = "education" # 大学は教育
        elif "公園" in station_name:
            icon_name = "leaf" # 公園は葉っぱ
        elif "アクアマリン" in station_name:
            icon_name = "picture" # 水族館は写真
        elif "灯台" in station_name:
            icon_name = "tower" # 灯台はタワー
        else:
            icon_name = "map-marker" # その他

        # マーカーの作成
        folium.Marker(
            coord, popup=f"{station_name}", 
            icon=folium.Icon(color=color, icon=icon_name, prefix='glyphicon')
        ).add_to(m)
        
        # 経路の描画
        if station_name in routes_dict:
            route = routes_dict[station_name]
            route_coords = [(G.nodes[node]['y'], G.nodes[node]['x']) for node in route]
            folium.PolyLine(
                route_coords, color=color, weight=4, opacity=0.8, popup=station_name
            ).add_to(m)

    st_folium(m, width=800, height=500)
