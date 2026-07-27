import sys
sys.stdout.reconfigure(encoding='utf-8')
import os
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
import numpy as np
import keras
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix

IMG_SIZE = (256, 256)
BATCH_SIZE = 16
LABELS_NAMES = {0: 'Covid-19', 1: 'Normal', 2: 'Pneumonia viral', 3: 'Pneumonia bacteriana'}

test_ds = keras.utils.image_dataset_from_directory(
    'Test',
    image_size=IMG_SIZE,
    batch_size=BATCH_SIZE,
    label_mode='categorical',
    shuffle=False,
)

best_model = keras.models.load_model('modelo_raiox.keras')
test_loss, test_acc = best_model.evaluate(test_ds, verbose=0)
print(f'Loss no teste:     {test_loss:.4f}')
print(f'Acurácia no teste: {test_acc:.2%}')

y_prob = best_model.predict(test_ds, verbose=0)
y_pred = np.argmax(y_prob, axis=1)
y_true = np.concatenate([np.argmax(labels, axis=1) for _, labels in test_ds])

print()
print('Matriz de confusão (linhas=real, colunas=previsto):')
print(confusion_matrix(y_true, y_pred))
print()
print(classification_report(y_true, y_pred, target_names=[LABELS_NAMES[i] for i in range(4)]))
