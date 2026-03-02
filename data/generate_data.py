import pandas as pd
import random


random.seed(42)


templates = {
    'billing': [
        'I was charged twice for my order last week',
        'My invoice shows the wrong amount',
        'I need a refund for the subscription I cancelled',
        'Why was my card declined when I tried to pay',
        'I did not authorize this charge on my account',
        'Can you send me a copy of my last invoice',
        'My payment failed but money was deducted from my bank',
    ],
    'technical': [
        'The app crashes every time I open it',
        'I cannot log in even with the correct password',
        'The page is not loading and shows a 500 error',
        'I keep getting an error when I try to upload a file',
        'The dashboard is not showing my data correctly',
        'Your API is returning a 403 forbidden response',
        'The mobile app is freezing on the home screen',
    ],
    'account': [
        'I forgot my password and cannot reset it',
        'I need to change the email address on my account',
        'My account was locked and I do not know why',
        'How do I delete my account and all my data',
        'I want to update my billing address',
        'Can I merge two accounts under one login',
        'I did not receive the verification email',
    ],
    'shipping': [
        'My order was supposed to arrive three days ago',
        'The tracking number shows delivered but I got nothing',
        'I received the wrong item in my package',
        'Can I change the delivery address for my order',
        'My package was marked returned to sender',
        'How long does standard shipping usually take',
        'My order has been stuck in processing for a week',
    ],
    'general': [
        'Do you offer a student or nonprofit discount',
        'I have a suggestion for improving your product',
        'What are your support hours',
        'I would like to leave feedback about my experience',
        'Can I speak with a human agent please',
        'How do I export all my data from the platform',
        'What is your privacy policy regarding user data',
    ]
}


rows = []
for category, texts in templates.items():
    for text in texts:
        # Add slight variations to increase dataset size
        rows.append({'text': text, 'category': category})
        rows.append({'text': text + ' Please help.', 'category': category})
        rows.append({'text': 'Hi, ' + text.lower(), 'category': category})
        rows.append({'text': text + ' This is urgent.', 'category': category})


random.shuffle(rows)


df = pd.DataFrame(rows)
df.to_csv('data/tickets.csv', index=False)


print(f'Generated {len(df)} tickets')
print(df['category'].value_counts())

