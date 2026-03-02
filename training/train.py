import argparse
import os
import pandas as pd
import joblib
from sklearn.pipeline import Pipeline
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report


# SageMaker passes these arguments automatically
parser = argparse.ArgumentParser()
parser.add_argument('--model-dir', type=str, default=os.environ.get('SM_MODEL_DIR', '.'))
parser.add_argument('--train', type=str, default=os.environ.get('SM_CHANNEL_TRAIN', 'data'))
args = parser.parse_args()


# Load data
data_path = os.path.join(args.train, 'tickets.csv')
df = pd.read_csv(data_path)


print(f'Loaded {len(df)} records')
print('Category distribution:')
print(df['category'].value_counts())


# Split into train and test sets
X_train, X_test, y_train, y_test = train_test_split(
    df['text'], df['category'],
    test_size=0.2,
    random_state=42,
    stratify=df['category']
)


# Build the pipeline
model = Pipeline([
    ('tfidf', TfidfVectorizer(
        max_features=5000,
        ngram_range=(1, 2),  # Capture single words and word pairs
        stop_words='english'
    )),
    ('clf', LogisticRegression(
        max_iter=1000,
        C=1.0,
        solver='lbfgs',
        multi_class='auto'
    ))
])


# Train
model.fit(X_train, y_train)


# Evaluate
y_pred = model.predict(X_test)
print('\nClassification Report:')
print(classification_report(y_test, y_pred))


accuracy = model.score(X_test, y_test)
print(f'Accuracy: {accuracy:.4f}')


# Save the model
model_path = os.path.join(args.model_dir, 'model.joblib')
joblib.dump(model, model_path)
print(f'Model saved to {model_path}')

