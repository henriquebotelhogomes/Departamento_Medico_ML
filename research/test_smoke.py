# -*- coding: utf-8 -*-
"""Smoke test do projeto Departamento Médico ML.

Verifica, sem treinar nada, que o ambiente está apto a executar os notebooks:
  1. Dependências (requirements.txt) importam corretamente.
  2. Estrutura de dados Dataset/{0..3} e Test/{0..3} existe e contém imagens.
  3. O modelo (ResNet50 + cabeça densa) pode ser construído e compilado.

Uso:
    python test_smoke.py      -> sai com código 0 se tudo OK, 1 caso contrário
    pytest test_smoke.py      -> também funciona como suíte pytest
"""
import os
import sys

os.environ.setdefault('TF_CPP_MIN_LOG_LEVEL', '3')

# Raiz do projeto = pasta deste arquivo (independe do cwd)
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))

IMG_SIZE = (256, 256)
NUM_CLASSES = 4
CLASS_DIRS = ['0', '1', '2', '3']
DATA_DIRS = ['Dataset', 'Test']
IMAGE_EXTS = {'.jpg', '.jpeg', '.png', '.webp', '.bmp'}


def test_imports():
    """Todas as dependências do requirements.txt precisam importar."""
    import importlib
    required = {
        'tensorflow': 'tensorflow',
        'keras': 'keras',
        'numpy': 'numpy',
        'cv2': 'opencv-python',
        'matplotlib': 'matplotlib',
        'seaborn': 'seaborn',
        'sklearn': 'scikit-learn',
    }
    missing = []
    for module, package in required.items():
        try:
            importlib.import_module(module)
        except ImportError:
            missing.append(f'{module} (pacote: {package})')
    assert not missing, 'Dependências ausentes: ' + ', '.join(missing)


def test_data_directories():
    """Dataset/ e Test/ devem ter as classes 0..3 com pelo menos 1 imagem cada."""
    problems = []
    for data_dir in DATA_DIRS:
        base = os.path.join(PROJECT_ROOT, data_dir)
        if not os.path.isdir(base):
            problems.append(f'Pasta "{data_dir}" não encontrada na raiz do projeto')
            continue
        for class_dir in CLASS_DIRS:
            class_path = os.path.join(base, class_dir)
            if not os.path.isdir(class_path):
                problems.append(f'Subpasta de classe "{data_dir}/{class_dir}" não encontrada')
                continue
            n_images = sum(
                1 for f in os.listdir(class_path)
                if os.path.splitext(f)[1].lower() in IMAGE_EXTS
            )
            if n_images == 0:
                problems.append(f'"{data_dir}/{class_dir}" não contém nenhuma imagem')
    assert not problems, 'Estrutura de dados inválida:\n  - ' + '\n  - '.join(problems)


def test_model_builds():
    """O modelo do notebook deve construir, compilar e prever sem treinar."""
    import numpy as np
    from tensorflow import keras
    from tensorflow.keras import layers
    from tensorflow.keras.applications import ResNet50
    from tensorflow.keras.applications.resnet50 import preprocess_input

    # Mesma arquitetura do notebook; weights=None evita baixar os pesos ImageNet
    base_model = ResNet50(weights=None, include_top=False, input_shape=IMG_SIZE + (3,))
    base_model.trainable = False

    data_augmentation = keras.Sequential([
        layers.RandomRotation(0.03),
        layers.RandomZoom(0.1),
        layers.RandomTranslation(0.05, 0.05),
        layers.RandomContrast(0.1),
    ], name='data_augmentation')

    inputs = keras.Input(shape=IMG_SIZE + (3,))
    x = data_augmentation(inputs)
    x = preprocess_input(x)
    x = base_model(x, training=False)
    x = layers.GlobalAveragePooling2D()(x)
    x = layers.Dropout(0.3)(x)
    x = layers.Dense(256, activation='relu')(x)
    x = layers.Dropout(0.3)(x)
    outputs = layers.Dense(NUM_CLASSES, activation='softmax')(x)

    model = keras.Model(inputs, outputs, name='classificador_raiox')
    model.compile(
        loss='categorical_crossentropy',
        optimizer=keras.optimizers.Adam(learning_rate=1e-3),
        metrics=['accuracy'],
    )

    # Uma passada de inferência com imagem aleatória confirma o grafo de ponta a ponta
    dummy = np.random.randint(0, 256, size=(1,) + IMG_SIZE + (3,)).astype('float32')
    probs = model.predict(dummy, verbose=0)
    assert probs.shape == (1, NUM_CLASSES), f'Shape de saída inesperado: {probs.shape}'
    assert abs(float(probs.sum()) - 1.0) < 1e-3, 'Softmax não soma 1'


def main():
    checks = [
        ('Importação das dependências', test_imports),
        ('Estrutura de dados (Dataset/ e Test/)', test_data_directories),
        ('Construção do modelo sem treino', test_model_builds),
    ]
    failed = False
    for name, check in checks:
        try:
            check()
            print(f'[PASS] {name}')
        except AssertionError as exc:
            print(f'[FAIL] {name}: {exc}')
            failed = True
        except Exception as exc:  # erro inesperado também reprova
            print(f'[FAIL] {name}: erro inesperado {type(exc).__name__}: {exc}')
            failed = True
    print()
    if failed:
        print('Smoke test FALHOU.')
        return 1
    print('Smoke test OK — ambiente pronto para executar os notebooks.')
    return 0


if __name__ == '__main__':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except AttributeError:
        pass
    sys.exit(main())
