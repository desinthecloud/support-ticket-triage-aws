import argparse
import os
import pandas as pd
import joblib
from sklearn.pipeline import Pipeline
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--model-dir', type=str, default=os.environ.get('SM_MODEL_DIR', '.'))
    parser.add_argument('--train', type=str, default=os.environ.get('SM_CHANNEL_TRAIN', 'data'))
    args = parser.parse_args()

    data_path = os.path.join(args.train, 'tickets.csv')
    df = pd.read_csv(data_path)

    print(f'Loaded {len(df)} records')
    print(df['category'].value_counts())

    X_train, X_test, y_train, y_test = train_test_split(
        df['text'], df['category'],
        test_size=0.2, random_state=42, stratify=df['category']
    )

    model = Pipeline([
        ('tfidf', TfidfVectorizer(max_features=5000, ngram_range=(1, 2), stop_words='english')),
        ('clf', LogisticRegression(max_iter=1000, C=1.0, solver='lbfgs', multi_class='auto'))
    ])

    model.fit(X_train, y_train)

    y_pred = model.predict(X_test)
    print(classification_report(y_test, y_pred))
    print(f'Accuracy: {model.score(X_test, y_test):.4f}')

    model_path = os.path.join(args.model_dir, 'model.joblib')
    joblib.dump(model, model_path)
    print(f'Model saved to {model_path}')

def input_fn(request_body, content_type):
    import json
    if content_type == 'text/csv':
        return [request_body.strip()]
    if content_type == 'application/json':
        data = json.loads(request_body)
        if isinstance(data, list):
            return data
        return [data]
    raise ValueError(f'Unsupported content type: {content_type}')

def model_fn(model_dir):
    import joblib
    import os
    return joblib.load(os.path.join(model_dir, 'model.joblib'))

def predict_fn(input_data, model):
    return model.predict(input_data)

