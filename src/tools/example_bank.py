"""
Curated few-shot examples of (informal proof → Lean 4 code) pairs.

Used to improve formalization quality via in-context learning.
"""

from __future__ import annotations

from typing import Any

EXAMPLES: list[dict[str, Any]] = [
    {
        "category": "arithmetic",
        "difficulty": "trivial",
        "informal": "Prove that 1 + 1 = 2.",
        "lean": """\
import Mathlib

theorem one_plus_one : 1 + 1 = 2 := by norm_num
""",
    },
    {
        "category": "number_theory",
        "difficulty": "easy",
        "informal": "Prove that for all natural numbers n, 0 ≤ n.",
        "lean": """\
import Mathlib

theorem zero_le_nat (n : ℕ) : 0 ≤ n := by omega
""",
    },
    {
        "category": "number_theory",
        "difficulty": "easy",
        "informal": "Prove that for any natural number n, n + 0 = n.",
        "lean": """\
import Mathlib

theorem add_zero_nat (n : ℕ) : n + 0 = n := by simp
""",
    },
    {
        "category": "algebra",
        "difficulty": "easy",
        "informal": "Prove that for all integers a, b: (a + b)² = a² + 2ab + b².",
        "lean": """\
import Mathlib

theorem sq_add (a b : ℤ) : (a + b) ^ 2 = a ^ 2 + 2 * a * b + b ^ 2 := by ring
""",
    },
    {
        "category": "number_theory",
        "difficulty": "medium",
        "informal": "Prove that the square root of 2 is irrational.",
        "lean": """\
import Mathlib.Data.Real.Irrational

theorem sqrt2_irrational : Irrational (Real.sqrt 2) := by
  exact irrational_sqrt_two
""",
    },
    {
        "category": "set_theory",
        "difficulty": "easy",
        "informal": "Prove that the empty set is a subset of any set.",
        "lean": """\
import Mathlib

theorem empty_subset (α : Type*) (S : Set α) : ∅ ⊆ S := by
  exact Set.empty_subset S
""",
    },
    {
        "category": "logic",
        "difficulty": "easy",
        "informal": "Prove that P implies P (identity).",
        "lean": """\
import Mathlib

theorem id_impl (P : Prop) : P → P := by
  intro h
  exact h
""",
    },
    {
        "category": "logic",
        "difficulty": "easy",
        "informal": "Prove that P ∧ Q implies Q ∧ P (commutativity of conjunction).",
        "lean": """\
import Mathlib

theorem and_comm' (P Q : Prop) : P ∧ Q → Q ∧ P := by
  intro ⟨hp, hq⟩
  exact ⟨hq, hp⟩
""",
    },
    {
        "category": "number_theory",
        "difficulty": "medium",
        "informal": "Prove that 2 is a prime number.",
        "lean": """\
import Mathlib

theorem two_prime : Nat.Prime 2 := by decide
""",
    },
    {
        "category": "analysis",
        "difficulty": "medium",
        "informal": "Prove that the absolute value of any real number is non-negative.",
        "lean": """\
import Mathlib

theorem abs_nonneg' (x : ℝ) : 0 ≤ |x| := by
  exact abs_nonneg x
""",
    },
    {
        "category": "algebra",
        "difficulty": "medium",
        "informal": "Prove that for all real numbers x: x * 0 = 0.",
        "lean": """\
import Mathlib

theorem mul_zero' (x : ℝ) : x * 0 = 0 := by
  exact mul_zero x
""",
    },
    {
        "category": "number_theory",
        "difficulty": "medium",
        "informal": "Prove that if n divides a and n divides b, then n divides a + b.",
        "lean": """\
import Mathlib

theorem dvd_add' (n a b : ℤ) (ha : n ∣ a) (hb : n ∣ b) : n ∣ a + b := by
  exact dvd_add ha hb
""",
    },
    {
        "category": "topology",
        "difficulty": "hard",
        "informal": "Prove that a constant function between topological spaces is continuous.",
        "lean": """\
import Mathlib.Topology.Basic
import Mathlib.Topology.Constructions

theorem const_continuous {X Y : Type*} [TopologicalSpace X] [TopologicalSpace Y]
    (c : Y) : Continuous (fun _ : X => c) := by
  exact continuous_const
""",
    },
    {
        "category": "linear_algebra",
        "difficulty": "medium",
        "informal": "Prove that the zero vector is in any subspace.",
        "lean": """\
import Mathlib.LinearAlgebra.Basic

theorem zero_mem_subspace {R M : Type*} [Ring R] [AddCommGroup M] [Module R M]
    (S : Submodule R M) : (0 : M) ∈ S := by
  exact S.zero_mem
""",
    },
    {
        "category": "order_theory",
        "difficulty": "easy",
        "informal": "Prove that for natural numbers, if a ≤ b and b ≤ c, then a ≤ c.",
        "lean": """\
import Mathlib

theorem le_trans_nat (a b c : ℕ) (hab : a ≤ b) (hbc : b ≤ c) : a ≤ c := by
  omega
""",
    },
]


def get_relevant_examples(
    query: str,
    n: int = 3,
    category: str | None = None,
    max_difficulty: str | None = None,
) -> list[dict[str, Any]]:
    """Return the most relevant few-shot examples for a query.

    Uses simple keyword matching. For better results, integrate with
    the MathlibIndex for embedding-based search.
    """
    difficulty_order = {"trivial": 0, "easy": 1, "medium": 2, "hard": 3}
    max_diff_val = difficulty_order.get(max_difficulty or "hard", 3)

    candidates = EXAMPLES
    if category:
        candidates = [e for e in candidates if e["category"] == category]
    candidates = [
        e for e in candidates if difficulty_order.get(e["difficulty"], 0) <= max_diff_val
    ]

    # Simple scoring: count keyword overlaps
    query_words = set(query.lower().split())
    scored: list[tuple[float, dict]] = []
    for ex in candidates:
        ex_words = set(ex["informal"].lower().split())
        overlap = len(query_words & ex_words)
        scored.append((overlap, ex))

    scored.sort(key=lambda x: x[0], reverse=True)
    return [ex for _, ex in scored[:n]]


def format_examples_for_prompt(examples: list[dict[str, Any]]) -> str:
    """Format examples as a prompt section."""
    if not examples:
        return ""
    parts = ["## Examples of Correct Lean 4 Proofs\n"]
    for i, ex in enumerate(examples, 1):
        parts.append(
            f"### Example {i}: {ex['informal']}\n"
            f"```lean\n{ex['lean'].strip()}\n```\n"
        )
    return "\n".join(parts)
