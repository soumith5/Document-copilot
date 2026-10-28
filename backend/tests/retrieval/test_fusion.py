from app.retrieval.fusion import reciprocal_rank_fusion


def test_single_list_preserves_relative_order():
    scores = reciprocal_rank_fusion([[10, 20, 30]])
    assert scores[10] > scores[20] > scores[30]


def test_item_in_multiple_lists_scores_higher_than_single_list_item():
    # id 1 is top-ranked in both lists; id 2 is top-ranked in only one.
    scores = reciprocal_rank_fusion([[1, 3], [1, 2]])
    assert scores[1] > scores[2]
    assert scores[1] > scores[3]


def test_empty_lists_produce_empty_scores():
    assert reciprocal_rank_fusion([]) == {}
    assert reciprocal_rank_fusion([[], []]) == {}


def test_larger_k_dampens_the_gap_between_ranks():
    scores_default = reciprocal_rank_fusion([[1, 2]])
    scores_high_k = reciprocal_rank_fusion([[1, 2]], k=1000)
    gap_default = scores_default[1] - scores_default[2]
    gap_high_k = scores_high_k[1] - scores_high_k[2]
    assert gap_high_k < gap_default