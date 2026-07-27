"""Re-treino no subconjunto Mendeley via feature extraction (rapido em CPU).

Estrategia CPU-friendly (equivalente a Fase 1 do notebook):
- Passa cada imagem UMA vez pela ResNet50 congelada (ImageNet) -> vetor 2048-d.
- Treina apenas a cabeca densa (256 -> 4) sobre as features (rapido, muitas epocas).
- Monta o modelo de inferencia completo e salva em modelo_raiox_mendeley.keras
  (NAO sobrescreve o modelo de 80%).
- Avalia no Test/ original (sem e com TTA) e compara com o baseline de 80%.
"""
import os, time, json, numpy as np, tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers
from tensorflow.keras.applications import ResNet50
from tensorflow.keras.applications.resnet50 import preprocess_input

TRAIN_DIR = "Dataset_mendeley"
TEST_DIR = "Test"
IMG_SIZE = (256, 256)
BATCH_SIZE = 32
SEED = 42
VALIDATION_SPLIT = 0.15
OUT_MODEL = "modelo_raiox_mendeley.keras"
RESULT_JSON = "_resultado_mendeley.json"
LABELS = {0: "Covid-19", 1: "Normal", 2: "Pneumonia viral", 3: "Pneumonia bacteriana"}


def log(msg):
    print(msg, flush=True)


# ---------------------------------------------------------------- datasets
log("== Carregando datasets ==")
train_ds = keras.utils.image_dataset_from_directory(
    TRAIN_DIR, validation_split=VALIDATION_SPLIT, subset="training",
    seed=SEED, image_size=IMG_SIZE, batch_size=BATCH_SIZE, label_mode="categorical")
val_ds = keras.utils.image_dataset_from_directory(
    TRAIN_DIR, validation_split=VALIDATION_SPLIT, subset="validation",
    seed=SEED, image_size=IMG_SIZE, batch_size=BATCH_SIZE, label_mode="categorical")
class_names = train_ds.class_names
log(f"  classes: {class_names}")

# ------------------------------------------------- extrator de features
base_model = ResNet50(weights="imagenet", include_top=False, input_shape=IMG_SIZE + (3,))
base_model.trainable = False
inp = keras.Input(shape=IMG_SIZE + (3,))
x = preprocess_input(inp)
x = base_model(x, training=False)
x = layers.GlobalAveragePooling2D()(x)
feat_model = keras.Model(inp, x, name="extrator_resnet50")


def extrair(ds, nome):
    t0 = time.time()
    Xs, Ys = [], []
    for i, (imgs, labels) in enumerate(ds):
        f = feat_model.predict(imgs, verbose=0)
        Xs.append(f)
        Ys.append(labels.numpy())
        if (i + 1) % 20 == 0:
            log(f"    {nome}: {i + 1} lotes...")
    X = np.concatenate(Xs).astype("float32")
    Y = np.concatenate(Ys).astype("float32")
    log(f"  {nome}: {X.shape[0]} amostras, {X.shape[1]}-d  ({time.time() - t0:.0f}s)")
    return X, Y


log("== Extraindo features (ResNet50 congelada) ==")
X_train, y_train = extrair(train_ds, "treino")
X_val, y_val = extrair(val_ds, "val")

# ------------------------------------------------------------- cabeca
log("== Treinando cabeca densa ==")
head = keras.Sequential([
    keras.Input(shape=(X_train.shape[1],)),
    layers.Dropout(0.3),
    layers.Dense(256, activation="relu"),
    layers.Dropout(0.3),
    layers.Dense(len(class_names), activation="softmax"),
], name="cabeca")
head.compile(optimizer=keras.optimizers.Adam(1e-3),
             loss="categorical_crossentropy", metrics=["accuracy"])

cbs = [
    keras.callbacks.EarlyStopping(monitor="val_loss", patience=20,
                                  restore_best_weights=True, verbose=1),
    keras.callbacks.ReduceLROnPlateau(monitor="val_loss", factor=0.5,
                                      patience=6, min_lr=1e-6, verbose=1),
]
hist = head.fit(X_train, y_train, validation_data=(X_val, y_val),
                epochs=200, batch_size=32, callbacks=cbs, verbose=2)
best_val = max(hist.history["val_accuracy"])
log(f"  melhor val_accuracy: {best_val:.4f}")

# ----------------------------------------------- modelo completo + save
full = keras.Model(feat_model.input, head(feat_model.output), name="classificador_raiox_mendeley")
full.save(OUT_MODEL)
log(f"== Modelo salvo em {OUT_MODEL} ==")

# --------------------------------------------------- avaliacao no Test/
log("== Avaliando no Test/ original ==")
test_ds = keras.utils.image_dataset_from_directory(
    TEST_DIR, image_size=IMG_SIZE, batch_size=BATCH_SIZE,
    label_mode="categorical", shuffle=False)
test_names = test_ds.class_names

# sem TTA
y_true, y_pred = [], []
for imgs, labels in test_ds:
    p = full.predict(imgs, verbose=0)
    y_pred.append(np.argmax(p, axis=1))
    y_true.append(np.argmax(labels.numpy(), axis=1))
y_true = np.concatenate(y_true)
y_pred = np.concatenate(y_pred)
acc = float(np.mean(y_true == y_pred))
log(f"  ACC sem TTA: {acc:.4f} ({acc:.1%})")

# com TTA (media de softmax sobre pequenas variacoes)
tta_layers = keras.Sequential([
    layers.RandomRotation(0.03),
    layers.RandomZoom(0.1),
    layers.RandomTranslation(0.05, 0.05),
    layers.RandomContrast(0.1),
])
N_TTA = 10
y_true2, y_pred2 = [], []
for imgs, labels in test_ds:
    probs = full.predict(imgs, verbose=0)
    for _ in range(N_TTA):
        aug = tta_layers(imgs, training=True)
        probs = probs + full.predict(aug, verbose=0)
    probs = probs / (N_TTA + 1)
    y_pred2.append(np.argmax(probs, axis=1))
    y_true2.append(np.argmax(labels.numpy(), axis=1))
y_true2 = np.concatenate(y_true2)
y_pred2 = np.concatenate(y_pred2)
acc_tta = float(np.mean(y_true2 == y_pred2))
log(f"  ACC com TTA ({N_TTA}x): {acc_tta:.4f} ({acc_tta:.1%})")

# matriz de confusao simples (TTA)
K = len(test_names)
cm = np.zeros((K, K), dtype=int)
for t, p in zip(y_true2, y_pred2):
    cm[t, p] += 1
log("  Matriz de confusao (TTA), linhas=verdadeiro, colunas=predito:")
log("     " + " ".join(f"{c:>4}" for c in test_names))
for i, row in enumerate(cm):
    log(f"  {test_names[i]:>2} " + " ".join(f"{v:>4}" for v in row))

# ------------------------------------------------------------- resultado
resultado = {
    "n_treino": int(X_train.shape[0]),
    "n_val": int(X_val.shape[0]),
    "melhor_val_accuracy": float(best_val),
    "test_acc_sem_tta": acc,
    "test_acc_com_tta": acc_tta,
    "baseline_80pct": 0.80,
    "epocas_treinadas": len(hist.history["loss"]),
}
with open(RESULT_JSON, "w", encoding="utf-8") as f:
    json.dump(resultado, f, indent=2, ensure_ascii=False)
log(f"== Resultado salvo em {RESULT_JSON} ==")
log(json.dumps(resultado, indent=2, ensure_ascii=False))
log("PRONTO.")
