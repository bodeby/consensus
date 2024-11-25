from typing import List
from torch import Tensor
import numpy as np

from consensus import AutoModelMember
from consensus import Tokenizer # todo: since AutoTokenizer is not inheritable just use base. 
from consensus import Configuration
from consensus import Ensemble

from transformers import AutoTokenizer


# create union vocabularies over one or more tokenizers
def create_union_vocabulary(tokenizers: List[Tokenizer]):
    # step 1: Create list of vocabularies in the tokenizers
    vocabularies = [tokenizer.get_vocab() for tokenizer in tokenizers]
    vocab_keys = [set(vocab.keys()) for vocab in vocabularies]

    # step 2: Iteratively compute the union of all vocabularies
    union_vocab = set()
    for keys in vocab_keys:
        union_vocab.update(keys)

    # step 3: Sort the union vocabulary for consistent indexing
    sorted_union_vocab = sorted(union_vocab)
    union_vocab_index = {token: idx for idx, token in enumerate(sorted_union_vocab)}

    return sorted_union_vocab, union_vocab_index

# create mapping from local tokenizer index to union index
def create_tokenizer_mapping(tokenizer: Tokenizer, vocab: Tensor, index):
    # grab vocabulary from tokenizer
    tk_vocab = tokenizer.get_vocab()

    # Step 4.1: Create mapping matrices for tokenizer 1
    tk_to_union = np.zeros((len(tk_vocab), len(vocab)), dtype=int)
    for token, t1_idx in tk_vocab.items():
        union_idx = index[token]
        tk_to_union[t1_idx, union_idx] = 1


def main():
    # Setup specialized Ensemble Member extending: AutoModelForCausalLM (transformers)
    m1 = AutoModelMember.from_pretrained("meta-llama/Llama-3.2-3B-Instruct")
    m2 = AutoModelMember.from_pretrained("Qwen/Qwen2.5-3B-Instruct")

    # Setup specialized Ensemle Tokenizers extending: AutoTokenizer (transformers)
    t1 = AutoTokenizer.from_pretrained("meta-llama/Llama-3.2-3B-Instruct")
    t2 = AutoTokenizer.from_pretrained("Qwen/Qwen2.5-3B-Instruct")

    # Create common vocabulary
    union_vocab, union_vocab_index = create_union_vocabulary([t1, t2])
    t1_mapping = create_tokenizer_mapping(
        tokenizer=t1, vocab=union_vocab, index=union_vocab_index
    )
    t2_mapping = create_tokenizer_mapping(
        tokenizer=t2, vocab=union_vocab, index=union_vocab_index
    )

    config = Configuration(temperature=0.7, voting_stragety="average_voting")
    ensemble = Ensemble(config)

    # add ensemble members
    ensemble.add_member(m1, t1, t1_mapping)
    ensemble.add_member(m2, t2, t2_mapping)

    # add union mpa
    ensemble.generate(prompt="Finish this sentence: The quick brown ...")

    print(ensemble)


if __name__ == "__main__":
    main()
