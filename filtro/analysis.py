import pyLDAvis.sklearn
from sklearn.decomposition import LatentDirichletAllocation
from sklearn.feature_extraction.text import TfidfVectorizer


def modelar_lda(conteudos):
    vectorizer_all = TfidfVectorizer(
        ngram_range=(1, 2),
        max_df=0.6,
        min_df=5,
        max_features=2000
    )

    features = vectorizer_all.fit_transform(conteudos)
    lda = LatentDirichletAllocation(n_components=10)

    lda.fit(features)

    modelo = pyLDAvis.sklearn.prepare(lda, features, vectorizer_all)

    saida = pyLDAvis.display(modelo)

    return saida.data
