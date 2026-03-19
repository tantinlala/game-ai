"""Tests for EFG solver features: unique infoset labels, SPNE filtering, and on-path merging."""

import os
import tempfile

import pygambit as gbt
import pytest

from game_ai.game.solver import GameSolver


# -- Fixtures --

PARTIFUL_EFG = """EFG 2 R "Partiful Monetization Dilemma" { "Partiful" "Users" }
p "Partiful Choice" 1 1 "Select Strategy" { "StatusQuo" "SaasModel" "TaxModel" "AdModel" } 0
p "Users vs StatusQuo" 2 1 "User Reaction" { "Stay" "Churn" } 0
t "Growth Wins" 1 "High Growth Low Revenue" { 2, 10 }
t "Obsolete" 2 "Lost to Giants" { -5, 5 }
p "Users vs SaaS" 2 2 "User Reaction" { "Stay" "Churn" } 0
t "Premium Success" 3 "Stable Revenue" { 8, 7 }
t "Niche Exit" 4 "User Flight to Free" { 1, 4 }
p "Users vs Tax" 2 3 "User Reaction" { "Stay" "Churn" } 0
t "Cash Cow" 5 "High Revenue" { 10, 6 }
t "Ticketing Churn" 6 "Lost to Luma" { 0, 8 }
p "Users vs Ads" 2 4 "User Reaction" { "Stay" "Churn" } 0
t "Ad Revenue" 7 "Short-term Gain" { 5, -2 }
t "Enshittification" 8 "Brand Death" { -10, 9 }"""

SIMPLE_SEQUENTIAL_EFG = """EFG 2 R "Simple Sequential" { "P1" "P2" }
p "" 1 1 "P1 Choice" { "L" "R" } 0
p "" 2 1 "P2 Choice" { "A" "B" } 0
t "" 1 "" { 3, 1 }
t "" 2 "" { 0, 0 }
t "" 3 "" { 1, 2 }"""

UNIQUE_INFOSET_LABELS_EFG = """EFG 2 R "Unique Labels" { "P1" "P2" }
p "" 1 1 "Choose" { "X" "Y" } 0
p "Node A" 2 1 "React" { "U" "D" } 0
t "" 1 "" { 2, 1 }
t "" 2 "" { 0, 3 }
p "Node B" 2 2 "React" { "U" "D" } 0
t "" 3 "" { 1, 2 }
t "" 4 "" { 3, 0 }"""


def _load_game(efg_content):
    """Load a pygambit game from EFG string."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.efg', delete=False) as f:
        f.write(efg_content)
        path = f.name
    try:
        return gbt.read_efg(path)
    finally:
        os.unlink(path)


# Imperfect information: P2 can't distinguish P1's action (same info set)
IMPERFECT_INFO_EFG = """EFG 2 R "Imperfect Info" { "P1" "P2" }
p "" 1 1 "P1Move" { "L" "R" } 0
p "After L" 2 1 "P2Move" { "A" "B" } 0
t "" 1 "" { 2, 1 }
t "" 2 "" { 0, 0 }
p "After R" 2 1 "P2Move" { "A" "B" } 0
t "" 3 "" { 0, 0 }
t "" 4 "" { 1, 2 }"""


# -- Unique infoset label tests --

@pytest.mark.unit
class TestUniqueInfosetLabels:
    """Tests for _get_unique_infoset_labels disambiguating duplicate labels."""

    def test_duplicate_infoset_labels_are_disambiguated(self):
        """When multiple infosets share a label, they get unique keys using node labels."""
        game = _load_game(PARTIFUL_EFG)
        users = game.players[1]
        labels = GameSolver._get_unique_infoset_labels(users)

        label_values = list(labels.values())
        assert len(label_values) == len(set(label_values)), \
            f"Labels should be unique but got: {label_values}"

    def test_disambiguated_labels_use_node_names(self):
        """Disambiguated labels should include the member node label."""
        game = _load_game(PARTIFUL_EFG)
        users = game.players[1]
        labels = GameSolver._get_unique_infoset_labels(users)

        label_values = list(labels.values())
        assert any("Users vs StatusQuo" in lbl for lbl in label_values)
        assert any("Users vs SaaS" in lbl for lbl in label_values)
        assert any("Users vs Tax" in lbl for lbl in label_values)
        assert any("Users vs Ads" in lbl for lbl in label_values)

    def test_unique_labels_left_unchanged(self):
        """Infosets with already-unique labels are not modified."""
        game = _load_game(PARTIFUL_EFG)
        partiful = game.players[0]
        labels = GameSolver._get_unique_infoset_labels(partiful)

        assert list(labels.values()) == ["Select Strategy"]

    def test_disambiguated_labels_in_formatted_equilibrium(self):
        """Formatted equilibria should use unique keys so no actions are lost."""
        game = _load_game(PARTIFUL_EFG)
        equilibria = list(gbt.nash.enumpure_solve(game).equilibria)

        eq_data = GameSolver._format_equilibrium(game, equilibria[0])
        users_strats = eq_data['strategies']['Users']

        # Users has 4 infosets × 2 actions = 8 strategy entries
        assert len(users_strats) == 8, \
            f"Expected 8 strategy entries (4 infosets × 2 actions), got {len(users_strats)}"


# -- Subgame perfect equilibrium tests --

@pytest.mark.unit
class TestSubgamePerfection:
    """Tests for _is_subgame_perfect filtering."""

    def test_filters_non_credible_threats(self):
        """NE sustained by non-credible off-path threats should be filtered."""
        result = GameSolver.solve_from_content(PARTIFUL_EFG)
        assert result.is_success()

        # All remaining equilibria should have Partiful playing SaasModel
        for eq in result.equilibria:
            partiful_strats = eq['strategies']['Partiful']
            active = [s for s, p in partiful_strats.items() if p > 0.99]
            assert any("SaasModel" in s for s in active), \
                f"SPNE should pick SaasModel, got: {active}"

    def test_credible_equilibrium_survives(self):
        """The backward-induction equilibrium should survive filtering."""
        result = GameSolver.solve_from_content(PARTIFUL_EFG)
        assert result.is_success()
        assert len(result.equilibria) >= 1

        eq = result.equilibria[0]
        assert eq['payoffs']['Partiful'] == pytest.approx(8.0)
        assert eq['payoffs']['Users'] == pytest.approx(7.0)

    def test_simple_sequential_game_spne(self):
        """Backward induction: P2 prefers A (payoff 2) over B (payoff 0), so P2 plays A.
        Given P2 plays A, P1 gets 3 from L vs 1 from R, so P1 plays L.
        SPNE: (P1→L, P2→A) with payoffs (3, 1)."""
        result = GameSolver.solve_from_content(SIMPLE_SEQUENTIAL_EFG)
        assert result.is_success()
        assert len(result.equilibria) >= 1

        # The SPNE should have payoffs (3, 1): P1 plays L, P2 plays A
        spne_payoffs = [(eq['payoffs']['P1'], eq['payoffs']['P2'])
                        for eq in result.equilibria]
        assert (3.0, 1.0) in [(pytest.approx(p1), pytest.approx(p2))
                               for p1, p2 in spne_payoffs]

    def test_is_subgame_perfect_rejects_irrational_offpath(self):
        """Directly test _is_subgame_perfect on equilibria with non-credible threats."""
        game = _load_game(PARTIFUL_EFG)
        equilibria = list(gbt.nash.enumpure_solve(game).equilibria)

        spne_count = sum(1 for eq in equilibria
                         if GameSolver._is_subgame_perfect(game, eq))
        all_count = len(equilibria)

        # Should filter some out (5 NE → fewer SPNE)
        assert spne_count < all_count, \
            f"Expected some equilibria to be filtered, but {spne_count}/{all_count} passed"

    def test_all_spne_have_optimal_offpath_actions(self):
        """Every SPNE should have Users playing best responses at all infosets."""
        game = _load_game(PARTIFUL_EFG)
        equilibria = list(gbt.nash.enumpure_solve(game).equilibria)
        spne = [eq for eq in equilibria
                if GameSolver._is_subgame_perfect(game, eq)]

        for eq in spne:
            behavior = eq.as_behavior() if hasattr(eq, 'as_behavior') else eq
            # Users at StatusQuo: Stay(10) > Churn(5) → must play Stay
            # Users at SaaS: Stay(7) > Churn(4) → must play Stay
            # Users at Tax: Churn(8) > Stay(6) → must play Churn
            # Users at Ads: Churn(9) > Stay(-2) → must play Churn
            users = game.players[1]
            for infoset in users.infosets:
                for action in infoset.actions:
                    prob = float(behavior[action])
                    node_label = list(infoset.members)[0].label
                    if "StatusQuo" in node_label:
                        if action.label == "Stay":
                            assert prob > 0.99
                    elif "SaaS" in node_label:
                        if action.label == "Stay":
                            assert prob > 0.99
                    elif "Tax" in node_label:
                        if action.label == "Churn":
                            assert prob > 0.99
                    elif "Ads" in node_label:
                        if action.label == "Churn":
                            assert prob > 0.99

    def test_degenerate_offpath_strategy_not_false_filtered(self):
        """When enumpure_solve returns all-zero probabilities for an off-path
        infoset, the equilibrium should NOT be incorrectly rejected.

        In the ICE Standoff game, Trump Final is off-path when Trump plays
        Withdraw/Scale Back. enumpure_solve returns (0,0,0) at Trump Final.
        The backward-induction SPNE is: Trump→Withdraw, Walz→(Pursue,GuardStandby),
        yielding Peaceful Exit (30, 70).
        """
        ICE_STANDOFF_EFG = """EFG 2 R "Minnesota ICE Standoff - Sequential Escalation" { "Trump Administration" "Gov. Tim Walz" }

    p "Trump Initial" 1 1 "Operation Metro Surge" { "Maintain Surge" "Withdraw/Scale Back" } 0

    p "Walz Legal" 2 1 "Legal Response" { "Pursue Injunctions" "No Legal Obstruction" } 0

    p "Walz Guard" 2 2 "Guard Deployment" { "Guard Shield (Blockade)" "Guard Standby (Security)" } 0

    p "Trump Final" 1 2 "Federal Reaction" { "Insurrection Act" "Economic Sanctions Only" "De-escalate" } 0

    t "Total Conflict" 1 "Outcome: Civil War" { 60, -100 }
    t "Economic Siege" 2 "Outcome: Funding Starvation" { 80, -70 }
    t "Federal Retreat" 3 "Outcome: State Sovereignty" { -30, 90 }

    t "Legal Victory" 4 "Outcome: Court Ordered Halt" { 20, 60 }
    t "Yielded Control" 5 "Outcome: Federal Dominance" { 100, 10 }

    t "Peaceful Exit" 6 "Outcome: Early De-escalation" { 30, 70 }"""

        result = GameSolver.solve_from_content(ICE_STANDOFF_EFG)
        assert result.is_success(), f"Expected SPNE but got error: {result.error}"
        assert len(result.equilibria) >= 1, "Should find at least one SPNE"

        # The unique SPNE ends at Peaceful Exit: Trump withdraws (30, 70)
        payoffs = [(eq['payoffs']['Trump Administration'], eq['payoffs']['Gov. Tim Walz'])
                   for eq in result.equilibria]
        assert (pytest.approx(30.0), pytest.approx(70.0)) in [
            (pytest.approx(p1), pytest.approx(p2)) for p1, p2 in payoffs
        ], f"Expected SPNE payoff (30, 70) but got: {payoffs}"

    def test_imperfect_info_no_spurious_filtering(self):
        """In a game with no proper subgames (besides the whole game),
        SPNE should equal NE — no equilibria should be filtered out."""
        game = _load_game(IMPERFECT_INFO_EFG)

        # P2's info set has 2 members, so no node below the root starts a
        # proper subgame. SPNE cannot refine beyond NE.
        raw = list(gbt.nash.enumpure_solve(game).equilibria)
        spne = [eq for eq in raw if GameSolver._is_subgame_perfect(game, eq)]

        assert len(spne) == len(raw), \
            f"No proper subgames exist, so all {len(raw)} NE should be SPNE, got {len(spne)}"

    def test_imperfect_info_multi_member_infoset(self):
        """Verify the game fixture actually has a multi-member info set."""
        game = _load_game(IMPERFECT_INFO_EFG)
        p2_infosets = list(game.players[1].infosets)
        assert len(p2_infosets) == 1
        assert len(list(p2_infosets[0].members)) == 2


# -- On-path merging tests --

@pytest.mark.unit
class TestOnPathMerging:
    """Tests for merging equilibria that differ only in off-path actions."""

    def test_partiful_game_merges_to_fewer_equilibria(self):
        """5 raw NE should merge down after SPNE filter + on-path merge."""
        game = _load_game(PARTIFUL_EFG)
        raw_equilibria = list(gbt.nash.enumpure_solve(game).equilibria)
        assert len(raw_equilibria) == 5, "Sanity check: game should have 5 raw pure NE"

        result = GameSolver.solve_from_content(PARTIFUL_EFG)
        assert len(result.equilibria) < len(raw_equilibria)

    def test_merged_equilibria_show_only_on_path_actions(self):
        """After merging, strategies should only contain on-path actions."""
        result = GameSolver.solve_from_content(PARTIFUL_EFG)
        assert result.is_success()

        for eq in result.equilibria:
            # Partiful has one on-path infoset (Select Strategy)
            partiful_strats = eq['strategies']['Partiful']
            active_partiful = [s for s, p in partiful_strats.items() if p > 0.99]
            assert len(active_partiful) == 1

            # Users should only have the on-path infoset shown
            users_strats = eq['strategies']['Users']
            active_users = [s for s, p in users_strats.items() if p > 0.99]
            assert len(active_users) == 1, \
                f"Should show only 1 on-path action for Users, got: {active_users}"

    def test_on_path_actions_extracts_correct_infosets(self):
        """_get_on_path_actions should identify the right reached infosets."""
        game = _load_game(PARTIFUL_EFG)
        equilibria = list(gbt.nash.enumpure_solve(game).equilibria)

        # Pick an equilibrium where Partiful plays SaasModel
        for eq in equilibria:
            eq_data = GameSolver._format_equilibrium(game, eq)
            partiful_active = [s for s, p in eq_data['strategies']['Partiful'].items()
                               if p > 0.99]
            if any("SaasModel" in s for s in partiful_active):
                on_path = GameSolver._get_on_path_actions(game, eq_data)

                # On-path for Users should only be "Users vs SaaS"
                users_on_path = on_path['Users']
                assert any("Users vs SaaS" in key for key in users_on_path.keys())
                assert not any("Users vs StatusQuo" in key for key in users_on_path.keys())
                assert not any("Users vs Tax" in key for key in users_on_path.keys())
                assert not any("Users vs Ads" in key for key in users_on_path.keys())
                return

        pytest.fail("No equilibrium with SaasModel found")

    def test_distinct_on_path_outcomes_not_merged(self):
        """Equilibria with different on-path outcomes should remain separate."""
        game = _load_game(UNIQUE_INFOSET_LABELS_EFG)
        raw_equilibria = list(gbt.nash.enumpure_solve(game).equilibria)

        # Format and merge
        formatted = [GameSolver._format_equilibrium(game, eq) for eq in raw_equilibria]
        merged = GameSolver._merge_efg_equilibria(game, formatted)

        # Each distinct on-path outcome should produce a separate entry
        payoff_sets = set()
        for eq in merged:
            payoffs = tuple(sorted(eq['payoffs'].items()))
            payoff_sets.add(payoffs)

        assert len(payoff_sets) == len(merged), \
            "Each merged equilibrium should have distinct payoffs"


# -- Integration: NFG games are unaffected --

@pytest.mark.unit
class TestNFGUnaffected:
    """Verify that NFG solving is not affected by EFG-specific changes."""

    def test_nfg_game_still_solves(self):
        """NFG games should solve normally without SPNE filtering or merging."""
        nfg = """NFG 1 R "Prisoner's Dilemma"
{ "Player 1" "Player 2" }

{
{ "Cooperate" "Defect" }
{ "Cooperate" "Defect" }
}

{
{ "Both Cooperate" 3, 3 }
{ "P1 Defects" 5, 0 }
{ "P2 Defects" 0, 5 }
{ "Both Defect" 1, 1 }
}
1 2 3 4"""
        result = GameSolver.solve_from_content(nfg)
        assert result.is_success()
        assert len(result.equilibria) >= 1

        eq = result.equilibria[0]
        assert 'Player 1' in eq['strategies']
        assert 'Player 2' in eq['strategies']
