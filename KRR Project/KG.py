import pandas as pd
import networkx as nx
import matplotlib
import matplotlib.pyplot as plt
from collections import defaultdict

matplotlib.use('Agg')


def parse_emotion_scores(score_string):
    scores = {}
    if not score_string or score_string.lower() == 'nan':
        return scores

    for item in score_string.split('|'):
        if ':' not in item:
            continue
        emotion, value = item.split(':', 1)
        try:
            scores[emotion.strip()] = float(value)
        except ValueError:
            continue
    return scores


def build_graph_from_data(data_list):
    G = nx.DiGraph()

    G.add_node("Movie", type="concept", size=4000)

    movie_freq = defaultdict(int)
    genre_freq = defaultdict(int)
    director_freq = defaultdict(int)
    emotion_freq = defaultdict(int)

    for row in data_list:
        title = str(row.get("Title", "")).strip()
        genres = str(row.get("Genre", "")).strip()
        director = str(row.get("Director", "")).strip()
        year = str(row.get("Release Year", "")).strip()
        emotion = str(row.get("predicted_emotion", "")).strip()
        scores = parse_emotion_scores(row.get("emotion_scores", ""))

        movie_node = f"{title} ({year})"
        movie_freq[movie_node] += 1
        G.add_node(
            movie_node,
            type="movie",
            size=1200 + movie_freq[movie_node] * 100
        )
        G.add_edge("Movie", movie_node, relationship="instance_of")

        if genres.lower() != "nan" and genres != "":
            for genre in genres.split(';'):
                genre = genre.strip()
                genre_freq[genre] += 1
                G.add_node(
                    genre,
                    type="genre",
                    size=800 + genre_freq[genre] * 200
                )
                G.add_edge(movie_node, genre, relationship="belongs_to")
                G.add_edge("Movie", genre, relationship="has_genre")

        if director.lower() != "nan" and director != "":
            director_freq[director] += 1
            G.add_node(
                director,
                type="director",
                size=1000 + director_freq[director] * 300
            )
            G.add_edge(director, movie_node, relationship="directed")

        emotion_freq[emotion] += 1
        confidence = scores.get(emotion, 1.0)
        G.add_node(
            emotion,
            type="emotion",
            size=1500 + emotion_freq[emotion] * 400
        )
        G.add_edge("Movie", emotion, relationship="evokes")
        G.add_edge(movie_node, emotion, relationship="triggers", weight=confidence)

        if director:
            G.add_edge(
                director,
                emotion,
                relationship="evokes_via",
                weight=confidence
            )

    return G


def plot_graph(G, output_path=None):
    plt.figure(figsize=(18, 14))
    pos = nx.spring_layout(G, k=2.8, iterations=100, seed=42)

    node_sizes = [G.nodes[n].get('size', 800) for n in G.nodes()]
    node_colors = []
    for n in G.nodes():
        t = G.nodes[n].get('type')
        if t == 'concept':       node_colors.append('yellow')
        elif t == 'emotion':     node_colors.append('lightcoral')
        elif t == 'movie':       node_colors.append('lightgreen')
        elif t == 'director':    node_colors.append('lightskyblue')
        elif t == 'genre':       node_colors.append('lightpink')

    nx.draw_networkx_nodes(G, pos, node_size=node_sizes, node_color=node_colors, alpha=0.9)
    nx.draw_networkx_edges(G, pos, alpha=0.5, arrows=True, arrowsize=20)

    labels = {}
    for n in G.nodes():
        node_type = G.nodes[n].get('type')
        node_size = G.nodes[n].get('size', 0)
        if node_type in ['movie', 'director', 'emotion', 'genre'] or node_size > 1500:
            labels[n] = n
    nx.draw_networkx_labels(G, pos, labels, font_size=9, font_weight='bold')

    edge_labels = {}
    for u, v, d in G.edges(data=True):
        if d['relationship'] in ['triggers', 'evokes', 'directed', 'belongs_to']:
            edge_labels[(u, v)] = d['relationship']
    nx.draw_networkx_edge_labels(G, pos, edge_labels, font_size=8)

    plt.title("Structured Knowledge Graph: Movies, Genres, Directors, Emotions", fontsize=16)
    plt.axis('off')
    plt.tight_layout()

    if output_path:
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        print(f"Graph saved as '{output_path}'")
        plt.close()


def main():
    INPUT_CSV = "movies_tagged.csv"
    OUTPUT_GRAPH_IMAGE = "movie_emotions_kg.png"
    MAX_MOVIES = 5

    df = pd.read_csv(INPUT_CSV)
    df = df.head(MAX_MOVIES)
    data_list = df.to_dict('records')

    G = build_graph_from_data(data_list)
    print("Knowledge Graph Built!")
    print(f"  Nodes: {G.number_of_nodes()}")
    print(f"  Edges: {G.number_of_edges()}")

    plot_graph(G, output_path=OUTPUT_GRAPH_IMAGE)


if __name__ == "__main__":
    main()
