
import tensorflow as tf
from transformers import TFGPT2Model, GPT2Config
import keras

class CustomEmbedding(keras.layers.Layer):
    def __init__(self, vocab_size, embed_dim):
        super(CustomEmbedding, self).__init__()
        self.token_emb = keras.layers.Embedding(input_dim=vocab_size, output_dim=embed_dim)
        self.pos_emb = keras.layers.Embedding(input_dim=7, output_dim=embed_dim)  # 假设序列长度为7

    def call(self, x):
        maxlen = tf.shape(x)[1]
        positions = tf.range(start=0, limit=maxlen, delta=1)
        positions = self.pos_emb(positions)
        x = self.token_emb(x)
        return x + positions



def gpt2_model(input_shape=(7, 20, 1), embed_dim=64, num_layers=4, num_heads=4, hidden_dim=64):
    # Define inputs
    inputs = keras.layers.Input(shape=input_shape)

    # Convert one-hot encoded input to integer indices
    x = tf.squeeze(inputs, axis=-1)  # Remove the last dimension (channels)
    input_ids = tf.argmax(x, axis=-1)

    # Generate attention mask
    attention_mask = tf.cast(tf.not_equal(input_ids, 0), dtype=tf.int32)

    # Custom embedding layer
    embedding_layer = CustomEmbedding(vocab_size=20, embed_dim=embed_dim)
    embedded_input = embedding_layer(input_ids)

    # Load pre-trained GPT-2 model configuration
    config = GPT2Config(
        vocab_size=20,  # Assume a vocabulary size of 20
        n_embd=embed_dim,
        n_layer=num_layers,
        n_head=num_heads,
        resid_pdrop=0.1,
        embd_pdrop=0.1,
        attn_pdrop=0.1,
        n_positions=input_shape[0]  # Assume sequence length of 7
    )

    # Load pre-trained GPT-2 model
    gpt2 = TFGPT2Model(config)

    # Replace GPT-2 embedding layers
    gpt2.transformer.wte = keras.layers.Embedding(input_dim=20, output_dim=embed_dim)
    gpt2.transformer.wpe = keras.layers.Embedding(input_dim=input_shape[0], output_dim=embed_dim)

    # Construct input dictionary
    model_inputs = {
        'input_ids': input_ids,
        'attention_mask': attention_mask
    }

    # Pass inputs to GPT-2 model
    x = gpt2(model_inputs)[0]  # Retrieve the last hidden state

    # Global average pooling
    x = keras.layers.GlobalAveragePooling1D()(x)
    
    # Layer normalization
    x = keras.layers.LayerNormalization(epsilon=1e-6)(x)
    
    # MLP head
    x = keras.layers.Dense(hidden_dim, activation='relu')(x)
    x = keras.layers.Dropout(0.5)(x)
    
    # Output layer
    outputs = keras.layers.Dense(1)(x)

    model = keras.Model(inputs=inputs, outputs=outputs)
    optimizer = keras.optimizers.Adam(learning_rate=0.0005)
    model.compile(loss='mean_squared_error', optimizer=optimizer, metrics=['mae'])

    return model
