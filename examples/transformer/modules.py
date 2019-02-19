
class Attention(nn.Module):
    "Scaled dot product attention"
    def __init__(self, p, scale):
        self.dropout = self.Dropout(p)
        self.scale = scale

    def spec(self, dim_query, dim_keys):
        self.dim_query = dim_query
        self.dim_keys = dim_keys
        return self

    def forward(self, query, key, value, mask):
        scores = query.dot(self.dim_key, key) / scale
        scores[mask] = -1e9
        p_attn = self.dropout(scores.softmax(dim_query))
        return value.dot(self.dim_keys, p_attn), p_attn

class MultiHeadedAttention(nn.Module):
    def __init__(self, heads, d_model, p=0.1):
        assert d_model % heads == 0
        d_k = d_model // heads
        proj = nn.Parameter(ntorch.zeros(3, heads, d_k, d_model))
        out_proj = nn.Parameter(torch.zeros(heads, d_k, d_model))

    def spec(self, dim_query, dim_keys, dim_hidden):
        self.dim_hidden = dim_hidden
        self.dim_query = dim_query
        self.dim_keys = dim_keys
        self.proj.spec(names=("qkv", "heads", "lower", dim_hidden))
        self.out_proj.spec(names=("heads", "lower", dim_hidden))
        return self

    def forward(self, query, key, value, mask):
        group = ntorch.stack([query, key, value], "qkv")
        query, key, value = self.proj.tensor.dot(self.dim_hidden, group).unbind("qkv")
        x, self.attn = self.attention(query, key, value, self.d_k, mask=mask)
        return self.out_proj.tensor.dot(("heads", "lower"), x)

class LabelSmoothing(nn.Module):
    def __init__(self, smoothing, size, padding_idx):
        self.size = size
        self.padding_idx = padding_idx
        self.smoothing = smoothing
        self.criterion = nn.KLDivLoss(reduction='sum')

        # Internal
        self._off_prob = self.smoothing / (self.size - 2)
        self._on_prob = 1.0 - self.smoothing

    def spec(self, dim_batch, dim_classes):
        self.dim_classes = dim_classes
        self.dim_batch = dim_batch
        self.criterion.spec(dim_classes)
        return self

    def forward(self, x, target):
        assert x.shape[self.dim_classes] == self.size
        target_dist = ntorch(x, names=x.dims).fill_(self._off_prob)
        target_dist[{self.dim_classes: target}] = self._on_prob
        target_dist[{self.dim_classes: self.padding_idx}] = 0
        on = {self.dim_batch: (target != self.padding_idx).nonzero(name="off")}
        return self.criterion(x[on], target_dist[on])


class Residual(nn.Module):
    """
    A residual connection followed by a layer norm.
    Note for code simplicity the norm is first as opposed to last.
    """
    def __init__(self, p):
        self.norm = nn.LayerNorm()
        self.dropout = nn.Dropout(p)

    def spec(self, dim_hidden):
        self.dim_hidden = dim_hidden
        self.norm.spec(dim_hidden)
        return self

    def forward(self, x, sublayer):
        "Apply residual connection to any sublayer with the same size."
        return x + self.dropout(sublayer(self.norm(x)))

class PositionwiseFeedForward(nn.Module):
    def __init__(self, input_dim, output_dim, hidden_dim, p):
        self.w_1 = nn.Linear(input_dim, hidden_dim)
        self.w_2 = nn.Linear(hidden_dim, output_dim)
        self.dropout = nn.Dropout(p)

    def spec(self, dim_hidden):
        self.dim_hidden = dim_hidden
        self.w_1.spec(dim_hidden, "internal")
        self.w_2.spec("internal", dim_hidden)
        return self

    def forward(self, x):
        return self.w_2(self.dropout(F.relu(self.w_1(x))))

MAX_LEN = 5000
class PositionalEmbeddings(nn.Module):
    def __init__(self, input_dim, output_dim, scale, p):
        self.dropout = nn.Dropout(p)
        self.lut =  nn.Embedding(input_dim, output_dim)
        self.scale = scale

    def spec(self, dim_length, dim_hidden):
        self.dim_length = dim_length
        self.dim_hidden = dim_hidden
        self.pe = self.pe(self.d_model)
        return self

    def pe(self):
        pe = ntorch.zeros(MAX_LEN, self.d_model,
                          names=(self.dim_length, self.dim_hidden))
        position = ntorch.arange(0, MAX_LEN,
                                 names=self.dim_length).float()
        shift = torch.arange(0, self.d_model, 2, names=self.dim_hidden)
        div_term = torch.exp(shift.float() * -(math.log(10000.0) / d_model))
        val = ntorch.mul(position, div_term)
        pe[{self.dim_hidden: shift}] = val.sin()
        pe[{self.dim_hidden: shift + 1}] = val.cos()
        return pe

    def forward(self, x):
        x = self.lut(x) * math.sqrt(self.scale)
        x = x + self.pe[{self.dim_length: slice(0, x.shape[self.dim_length])}]
        return self.dropout(x)