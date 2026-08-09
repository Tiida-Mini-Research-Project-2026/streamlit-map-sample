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
    "草野駅": (37.0874, 140.9178)
}

# 2. 道路網データの取得（自転車用、高専を中心に半径7km）
@st.cache_resource
def load_bike_graph():
    # アップロードしたファイルから直接読み込む（API通信をしない）
    return ox.load_graphml("bike_graph.graphml")

with st.spinner("自転車用の道路網データを取得中...（少し時間がかかります）"):
    G = load_bike_graph()

# 高専の最寄りノードを取得
dest_node = ox.nearest_nodes(G, X=kosen_coord[1], Y=kosen_coord[0])

# 3. ルートと距離の計算
results = []
routes_dict = {}

for station_name, coord in stations.items():
    # 各駅の最寄りノード
    orig_node = ox.nearest_nodes(G, X=coord[1], Y=coord[0])
    
    # 経路と距離の計算
    try:
        route = nx.shortest_path(G, orig_node, dest_node, weight='length')
        distance_m = nx.shortest_path_length(G, orig_node, dest_node, weight='length')
        distance_km = round(distance_m / 1000, 2) # kmに変換して小数第2位まで
        
        routes_dict[station_name] = route
        results.append({"駅名": station_name, "距離 (km)": distance_km})
    except nx.NetworkXNoPath:
        st.warning(f"{station_name}からのルートが見つかりませんでした。")

# 結果をデータフレーム化して距離順に並べ替え
df_results = pd.DataFrame(results).sort_values("距離 (km)")

# 4. 画面レイアウト（左に表、右に地図）
col1, col2 = st.columns([1, 2])

with col1:
    st.subheader("📊 距離の比較")
    st.dataframe(df_results, hide_index=True, use_container_width=True)
    st.info("※距離は地図上の道路網に沿った最短距離です。")

with col2:
    st.subheader("🗺️ ルートマップ")
    # 地図の初期化（高専を中心に）
    m = folium.Map(location=kosen_coord, zoom_start=13)
    
    # 高専のマーカー（星マーク）
    folium.Marker(
        kosen_coord, popup="福島高専", 
        icon=folium.Icon(color="red", icon="star")
    ).add_to(m)

    # 各駅からのルートを描画するための色リスト
    colors = ["blue", "green", "purple", "orange"]
    
    for i, (station_name, coord) in enumerate(stations.items()):
        color = colors[i % len(colors)]
        
        # 駅マーカー
        folium.Marker(
            coord, popup=f"{station_name}駅", 
            icon=folium.Icon(color=color, icon="info-sign")
        ).add_to(m)
        
        # 経路の描画
        if station_name in routes_dict:
            route = routes_dict[station_name]
            route_coords = [(G.nodes[node]['y'], G.nodes[node]['x']) for node in route]
            folium.PolyLine(
                route_coords, color=color, weight=4, opacity=0.8, popup=station_name
            ).add_to(m)

    st_folium(m, width=800, height=500)
