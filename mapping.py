import streamlit as st
import folium
from streamlit_folium import st_folium
import networkx as nx
import osmnx as ox
# 1. 地点データの定義（緯度・経度）
locations = {
    "いわき駅": (37.058, 140.8923),
    "福島高専": (37.03357748058106, 140.8908041370153)
}
st.title("最短経路可視化アプリ（道路網版）")
# 2. 道路網データの取得（キャッシュ化して高速化）
@st.cache_resource
def load_graph():
    # 2点の中間地点を計算
    center_lat = (locations["いわき駅"][0] + locations["福島高専"][0]) / 2
    center_lon = (locations["いわき駅"][1] + locations["福島高専"][1]) / 2
    # 中間地点から半径3kmの道路網（自動車用）を取得
    # ※ 徒歩ルートにする場合は network_type='walk' にします
    G = ox.graph_from_point((center_lat, center_lon), dist=3000, network_type='drive')
    return G
with st.spinner("道路網データを取得・構築中...（初回は少し時間がかかります）"):
    G = load_graph()
# 3. グラフ上の最寄りノードの特定
# 注意: nearest_nodes は (グラフ, X(経度), Y(緯度)) の順で渡す必要があります
orig_node = ox.nearest_nodes(G, X=locations["いわき駅"][1], Y=locations["いわき駅"][0])
dest_node = ox.nearest_nodes(G, X=locations["福島高専"][1], Y=locations["福島高専"][0])
# 4. 最短経路の計算
# 実際の道路の長さ（weight='length'）を基準に計算
route = nx.shortest_path(G, orig_node, dest_node, weight='length')
# 5. 地図と経路の描画
center_lat = (locations["いわき駅"][0] + locations["福島高専"][0]) / 2
center_lon = (locations["いわき駅"][1] + locations["福島高専"][1]) / 2
m = folium.Map(location=[center_lat, center_lon], zoom_start=14)
# 経路の座標リストを作成 (ノードデータから y=緯度, x=経度 を抽出)
route_coords = [(G.nodes[node]['y'], G.nodes[node]['x']) for node in route]
# スタートとゴールのマーカーを配置
folium.Marker(locations["いわき駅"], popup="いわき駅", icon=folium.Icon(color="blue")).add_to(m)
folium.Marker(locations["福島高専"], popup="福島高専", icon=folium.Icon(color="red")).add_to(m)
# 経路を青い線で引く
folium.PolyLine(route_coords, color="blue", weight=5, opacity=0.8).add_to(m)
# 6. Streamlitへの表示
st_folium(m, width=700, height=500)
