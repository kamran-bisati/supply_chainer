import numpy as np
import joblib
import os
import torch
import json
import time
from typing import List, Dict, Any, Optional, Tuple
import pandas as pd


# ============================================================
# PRODUCTION ARTIFACT PATHS
# ============================================================

# P50 / P85 / P95 models
MODEL_P50_PATH = "./Execution/risk_model_p50.pkl"
MODEL_P85_PATH = "./Execution/risk_model_p85.pkl"
MODEL_P95_PATH = "./Execution/risk_model_p95.pkl"

# Legacy model path.
# Kept for backward compatibility.
LEGACY_MODEL_PATH = "./Execution/risk_model.pkl"

ENCODER_PATH = "./Execution/label_encoders.pkl"
NLP_ANCHORS_PATH = "./Execution/nlp_anchors.pt"
CALIBRATION_PATH = "./Execution/calibration_profiles.json"


# ============================================================
# THREAT INTELLIGENCE PREDICTOR
# ============================================================

class ThreatIntelligencePredictor:
    """
    Supplychainer Quantile ML Decision Brain.

    V4:
    - P50 / P85 / P95 quantile prediction
    - Statistically defensible calibration
    - Geographic hub intelligence
    - P85 retained as the routing / legacy signal
    - Existing NLP + CARF pipeline remains unchanged
    """

    def __init__(self, lazy_load=False):

        self.is_trained = False

        # ----------------------------------------------------
        # Three production quantile models
        # ----------------------------------------------------

        self.model_p50 = None
        self.model_p85 = None
        self.model_p95 = None

        # ----------------------------------------------------
        # Legacy alias
        #
        # Existing code may still reference:
        # self.model
        #
        # Keep it pointing to P85.
        # ----------------------------------------------------

        self.model = None

        self.encoders = None
        self.profiles = {}

        # ----------------------------------------------------
        # Geographic hub mapping
        # ----------------------------------------------------

        self.hub_map = {
            "Seattle": "Seattle Port",
            "Portland": "Portland Terminal",
            "San Francisco": "San Francisco Port",
            "Los Angeles": "Los Angeles Port",
            "Salt Lake City": "Salt Lake City Hub",
            "Denver": "Denver Terminal",
            "Phoenix": "Phoenix Logistics",
            "Dallas": "Dallas Corridor",
            "Houston": "Houston Port",
            "Chicago": "Chicago Rail Hub",
            "St. Louis": "St. Louis Hub",
            "Atlanta": "Atlanta Air Hub",
            "Miami": "Miami Port",
            "New York": "New York Port",
            "Boston": "Boston Terminal",
            "Mumbai": "Mumbai Port",
            "Kochi": "Kochi Port",
            "Delhi": "Delhi Air Cargo",
            "Chennai": "Chennai Port"
        }

        if not lazy_load:
            self.warmup()


    # ========================================================
    # WARMUP
    # ========================================================

    def warmup(self):

        if self.is_trained:
            return

        print(
            "[PREDICTOR] Starting multi-quantile warmup..."
        )

        # ----------------------------------------------------
        # Encoder is mandatory
        # ----------------------------------------------------

        if not os.path.exists(ENCODER_PATH):

            print(
                "[PREDICTOR] CRITICAL: "
                "Production encoders missing. "
                "Running deterministic fallback mode."
            )

            return

        # ----------------------------------------------------
        # Check for new three-model architecture
        # ----------------------------------------------------

        p50_exists = os.path.exists(
            MODEL_P50_PATH
        )

        p85_exists = os.path.exists(
            MODEL_P85_PATH
        )

        p95_exists = os.path.exists(
            MODEL_P95_PATH
        )

        # ----------------------------------------------------
        # Load new multi-quantile models
        # ----------------------------------------------------

        if p50_exists and p85_exists and p95_exists:

            try:

                print(
                    "[PREDICTOR] Loading P50 model..."
                )

                self.model_p50 = joblib.load(
                    MODEL_P50_PATH
                )

                print(
                    "[PREDICTOR] Loading P85 model..."
                )

                self.model_p85 = joblib.load(
                    MODEL_P85_PATH
                )

                print(
                    "[PREDICTOR] Loading P95 model..."
                )

                self.model_p95 = joblib.load(
                    MODEL_P95_PATH
                )

                # ------------------------------------------------
                # Backward compatibility:
                # self.model = P85
                # ------------------------------------------------

                self.model = self.model_p85

                print(
                    "[PREDICTOR] P50 / P85 / P95 models loaded."
                )

            except Exception as e:

                print(
                    f"[PREDICTOR] Multi-quantile model "
                    f"loading failed: {e}"
                )

                self.model_p50 = None
                self.model_p85 = None
                self.model_p95 = None
                self.model = None

        # ----------------------------------------------------
        # Legacy fallback
        # ----------------------------------------------------

        elif os.path.exists(LEGACY_MODEL_PATH):

            try:

                print(
                    "[PREDICTOR] Multi-quantile models "
                    "not found."
                )

                print(
                    "[PREDICTOR] Loading legacy P85 model..."
                )

                self.model_p85 = joblib.load(
                    LEGACY_MODEL_PATH
                )

                self.model = self.model_p85

                print(
                    "[PREDICTOR] Legacy P85 model loaded."
                )

            except Exception as e:

                print(
                    f"[PREDICTOR] Legacy model loading "
                    f"failed: {e}"
                )

                return

        else:

            print(
                "[PREDICTOR] CRITICAL: No production "
                "ML model found."
            )

            return

        # ----------------------------------------------------
        # Load encoders
        # ----------------------------------------------------

        try:

            self.encoders = joblib.load(
                ENCODER_PATH
            )

            self.is_trained = True

            print(
                "[PREDICTOR] Label encoders loaded."
            )

        except Exception as e:

            print(
                f"[PREDICTOR] Encoder loading failed: {e}"
            )

            self.is_trained = False
            return

        # ====================================================
        # CALIBRATION PROFILES
        # ====================================================

        if os.path.exists(CALIBRATION_PATH):

            try:

                with open(
                    CALIBRATION_PATH,
                    "r"
                ) as f:

                    self.profiles = json.load(f)

                print(
                    f"Calibration Layer: Loaded "
                    f"{len(self.profiles)} mode profiles "
                    f"from historical p5/p95 analysis."
                )

            except Exception as e:

                print(
                    f"WARNING: Calibration profiles "
                    f"could not be loaded: {e}"
                )

                self.profiles = {}

        else:

            print(
                "WARNING: Calibration profiles missing. "
                "Using defensive fallbacks."
            )

            self.profiles = {}

        print(
            "[PREDICTOR] Supplychainer V4 Brain Loaded."
        )

        print(
            "[PREDICTOR] Quantiles: P50 / P85 / P95"
        )


    # ========================================================
    # FEATURE ENCODING
    # ========================================================

    def _encode_feature(
        self,
        value: str,
        key: str
    ) -> int:

        encoder = self.encoders[key]

        classes = list(
            encoder.classes_
        )

        # ----------------------------------------------------
        # Resolve geographic node to canonical hub
        # ----------------------------------------------------

        if key in [
            "Origin_Node",
            "Destination_Node"
        ]:

            resolved = self.hub_map.get(
                value,
                value
            )

            if resolved in classes:

                return encoder.transform(
                    [resolved]
                )[0]

        # ----------------------------------------------------
        # Direct match
        # ----------------------------------------------------

        if value in classes:

            return encoder.transform(
                [value]
            )[0]

        # ----------------------------------------------------
        # Defensive fallback
        # ----------------------------------------------------

        return encoder.transform(
            [classes[0]]
        )[0]


    # ========================================================
    # CALIBRATION HELPER
    # ========================================================

    def _get_calibration_profile(
        self,
        transport_mode: str
    ) -> Dict[str, float]:

        mode_key = transport_mode.lower()

        profile = self.profiles.get(
            mode_key,
            {
                "floor": 0.0,
                "cap": 240.0
            }
        )

        floor = float(
            profile.get(
                "floor",
                0.0
            )
        )

        cap = float(
            profile.get(
                "cap",
                240.0
            )
        )

        # Defensive protection
        floor = max(
            0.0,
            floor
        )

        cap = max(
            floor,
            cap
        )

        return {
            "floor": floor,
            "cap": cap
        }


    # ========================================================
    # QUANTILE CALIBRATION
    # ========================================================

    def _calibrate_quantile(
        self,
        raw_prediction: float,
        quantile_name: str,
        floor: float,
        cap: float
    ) -> float:

        raw_prediction = max(
            0.0,
            float(raw_prediction)
        )

        # ----------------------------------------------------
        # P50
        #
        # P50 represents the typical / median estimate.
        # We do NOT force it up to the historical p5 floor.
        # ----------------------------------------------------

        if quantile_name == "p50":

            calibrated = min(
                raw_prediction,
                cap
            )

            return max(
                0.0,
                calibrated
            )

        # ----------------------------------------------------
        # P85 / P95
        #
        # Preserve the existing systemic-friction floor.
        # ----------------------------------------------------

        calibrated = min(
            raw_prediction,
            cap
        )

        calibrated = max(
            calibrated,
            floor
        )

        return calibrated


    # ========================================================
    # PREDICT WORST CASE / MULTI-QUANTILE DELAY
    # ========================================================

    def predict_worst_case_delay(
        self,
        origin: str,
        destination: str,
        transport_mode: str,
        leg_type: str = "Global_Freight",
        condition_flag: str = "Clear",
        nlp_score: float = 0.0
    ) -> Dict[str, Any]:

        """
        Multi-quantile prediction.

        Returns:
            P50 = typical expected delay
            P85 = operational risk / routing signal
            P95 = high-tail delay estimate

        P85 remains exposed through:
            final_delay_presented

        This preserves compatibility with the existing
        RouteRecommender.
        """

        # ====================================================
        # DETERMINISTIC FALLBACK
        # ====================================================

        if not self.is_trained:

            mode_key = transport_mode.lower()

            priors = {
                "road": 2.5,
                "sea": 48.0,
                "air": 12.0,
                "rail": 18.0
            }

            p50 = priors.get(
                mode_key,
                12.0
            )

            # Conservative fallback bands.
            p85 = p50 * 1.5
            p95 = p50 * 2.0

            return {
                "raw_quantiles": {
                    "p50": round(p50, 2),
                    "p85": round(p85, 2),
                    "p95": round(p95, 2)
                },

                "quantiles": {
                    "p50": round(p50, 2),
                    "p85": round(p85, 2),
                    "p95": round(p95, 2)
                },

                # Backward-compatible P85 fields
                "raw_model_prediction": round(
                    p85,
                    2
                ),

                "calibrated_delay": round(
                    p85,
                    2
                ),

                "baseline_systemic_friction": round(
                    p85,
                    2
                ),

                "final_delay_presented": round(
                    p85,
                    2
                ),

                "calibration_reason":
                    "Deterministic Operational Prior "
                    "(Engine Warming)",

                "p_quantile": 0.85,

                "is_defensible": True
            }


        # ====================================================
        # ML INFERENCE
        # ====================================================

        try:

            # ------------------------------------------------
            # Encode input features
            # ------------------------------------------------

            feat_origin = self._encode_feature(
                origin,
                "Origin_Node"
            )

            feat_dest = self._encode_feature(
                destination,
                "Destination_Node"
            )

            feat_mode = self._encode_feature(
                transport_mode,
                "Transport_Mode"
            )

            feat_leg = self._encode_feature(
                leg_type,
                "Leg_Type"
            )

            feat_cond = self._encode_feature(
                condition_flag,
                "Condition_Flag"
            )

            # ------------------------------------------------
            # Build ML input
            # ------------------------------------------------

            X_input = pd.DataFrame([
                {
                    "Leg_Type": feat_leg,
                    "Origin_Node": feat_origin,
                    "Destination_Node": feat_dest,
                    "Transport_Mode": feat_mode,
                    "Condition_Flag": feat_cond,
                    "NLP_Severity_Score": nlp_score
                }
            ])


            # =================================================
            # RAW QUANTILE INFERENCE
            # =================================================

            # -------------------------------------------------
            # P50
            # -------------------------------------------------

            if self.model_p50 is not None:

                raw_p50 = float(
                    self.model_p50.predict(
                        X_input
                    )[0]
                )

            else:

                # Legacy-model fallback.
                # Do NOT pretend legacy P85 is P50.
                raw_p50 = 0.0


            # -------------------------------------------------
            # P85
            # -------------------------------------------------

            if self.model_p85 is not None:

                raw_p85 = float(
                    self.model_p85.predict(
                        X_input
                    )[0]
                )

            elif self.model is not None:

                raw_p85 = float(
                    self.model.predict(
                        X_input
                    )[0]
                )

            else:

                raw_p85 = 0.0


            # -------------------------------------------------
            # P95
            # -------------------------------------------------

            if self.model_p95 is not None:

                raw_p95 = float(
                    self.model_p95.predict(
                        X_input
                    )[0]
                )

            else:

                # Legacy fallback.
                # Do not fabricate a P95 multiplier.
                raw_p95 = raw_p85


            # ------------------------------------------------
            # Remove impossible negative predictions
            # ------------------------------------------------

            raw_p50 = max(
                0.0,
                raw_p50
            )

            raw_p85 = max(
                0.0,
                raw_p85
            )

            raw_p95 = max(
                0.0,
                raw_p95
            )


            # =================================================
            # CALIBRATION
            # =================================================

            profile = self._get_calibration_profile(
                transport_mode
            )

            floor = profile["floor"]
            cap = profile["cap"]


            calibrated_p50 = (
                self._calibrate_quantile(
                    raw_p50,
                    "p50",
                    floor,
                    cap
                )
            )

            calibrated_p85 = (
                self._calibrate_quantile(
                    raw_p85,
                    "p85",
                    floor,
                    cap
                )
            )

            calibrated_p95 = (
                self._calibrate_quantile(
                    raw_p95,
                    "p95",
                    floor,
                    cap
                )
            )


            # =================================================
            # QUANTILE ORDERING
            # =================================================

            # Quantiles should satisfy:
            #
            # P50 <= P85 <= P95
            #
            # The individual models are trained separately,
            # so small crossing can occasionally happen.
            #
            # This monotonic post-processing guarantees a
            # valid displayed band.

            calibrated_p50 = min(
                calibrated_p50,
                calibrated_p85
            )

            calibrated_p95 = max(
                calibrated_p95,
                calibrated_p85
            )


            # =================================================
            # EXPLAINABILITY
            # =================================================

            reason_parts = []

            if calibrated_p85 == floor:

                reason_parts.append(
                    f"Baseline Operational Friction "
                    f"(Historical p5: {floor}h)"
                )

            if raw_p85 > cap:

                reason_parts.append(
                    f"Operational Cap Applied "
                    f"(Historical p95 Bound: {cap}h)"
                )

            if not reason_parts:

                reason_parts.append(
                    "Multi-Quantile Risk Prediction"
                )

            reason = " + ".join(
                reason_parts
            )


            # =================================================
            # RETURN MULTI-QUANTILE RESULT
            # =================================================

            return {

                # ------------------------------------------------
                # Raw predictions before calibration
                # ------------------------------------------------

                "raw_quantiles": {
                    "p50": round(
                        raw_p50,
                        2
                    ),
                    "p85": round(
                        raw_p85,
                        2
                    ),
                    "p95": round(
                        raw_p95,
                        2
                    )
                },

                # ------------------------------------------------
                # Final calibrated quantiles
                # ------------------------------------------------

                "quantiles": {
                    "p50": round(
                        calibrated_p50,
                        2
                    ),
                    "p85": round(
                        calibrated_p85,
                        2
                    ),
                    "p95": round(
                        calibrated_p95,
                        2
                    )
                },

                # ------------------------------------------------
                # Backward-compatible P85 fields
                # ------------------------------------------------

                "raw_model_prediction": round(
                    raw_p85,
                    2
                ),

                "calibrated_delay": round(
                    calibrated_p85,
                    2
                ),

                "baseline_systemic_friction": round(
                    floor,
                    2
                ),

                # IMPORTANT:
                # Existing route engine uses this field.
                # It remains P85.

                "final_delay_presented": round(
                    calibrated_p85,
                    2
                ),

                "calibration_reason": reason,

                "p_quantile": 0.85,

                "is_defensible": True
            }


        # ====================================================
        # INFERENCE ERROR
        # ====================================================

        except Exception as e:

            print(
                f"Calibration Inference Error: {e}"
            )

            return {

                "raw_quantiles": {
                    "p50": 0.0,
                    "p85": 0.0,
                    "p95": 0.0
                },

                "quantiles": {
                    "p50": 0.0,
                    "p85": 0.0,
                    "p95": 0.0
                },

                "raw_model_prediction": 0.0,

                "calibrated_delay": 0.0,

                "baseline_systemic_friction": 0.0,

                "final_delay_presented": 0.0,

                "calibration_reason":
                    "Inference Error",

                "p_quantile": 0.85,

                "is_defensible": False
            }


# ============================================================
# CONTRASTIVE NLP ENGINE
# ============================================================

class ContrastiveNLPEngine:
    """
    Stage 2: PRODUCTION Contrastive NLP Brain.
    """

    def __init__(self, lazy_load=False):

        self._ready = False

        self.noise_floor = 0.04

        self.calibration_multiplier = 0.35

        if not lazy_load:
            self.warmup()


    def warmup(self):

        if self._ready:
            return

        print(
            "[NLP ENGINE] Starting warmup..."
        )

        try:

            from sentence_transformers import (
                SentenceTransformer,
                util
            )

            self.model = SentenceTransformer(
                "all-MiniLM-L6-v2"
            )

            self.util = util

            if os.path.exists(
                NLP_ANCHORS_PATH
            ):

                anchors = torch.load(
                    NLP_ANCHORS_PATH
                )

                self.disaster_matrix = (
                    anchors["disaster_matrix"]
                )

                self.safe_matrix = (
                    anchors["safe_matrix"]
                )

                self._ready = True

                print(
                    "NLP Brain: "
                    "Loaded Historical Anchor Matrix."
                )

            else:

                self._ready = False

        except Exception as e:

            print(
                f"[NLP ENGINE] Warmup failed: {e}"
            )

            self._ready = False


    def get_semantic_score(
        self,
        news_text: str
    ) -> float:

        if not self._ready:
            return 0.0

        if (
            not news_text
            or len(news_text.strip()) < 5
        ):
            return 0.0

        chunks = [
            news_text[i:i + 256]
            for i in range(
                0,
                len(news_text),
                256
            )
        ]

        chunk_embeddings = self.model.encode(
            chunks,
            convert_to_tensor=True
        )

        d_scores = self.util.cos_sim(
            chunk_embeddings,
            self.disaster_matrix
        )

        s_scores = self.util.cos_sim(
            chunk_embeddings,
            self.safe_matrix
        )

        margin = (
            float(
                np.max(
                    d_scores.cpu().numpy()
                )
            )
            -
            float(
                np.max(
                    s_scores.cpu().numpy()
                )
            )
        )

        if margin >= self.noise_floor:
            return 0.0

        return float(
            min(
                1.0,
                margin * self.calibration_multiplier
            )
        )


# ============================================================
# CARF FILTER
# ============================================================

class CARFFilter:
    """
    Stage 3:
    TRUE CARF (Context-Aware Relevance Filter).
    """

    def __init__(self):

        self.relevance_map = {
            "air": [
                "airport",
                "flight",
                "airspace",
                "aviation",
                "sky",
                "terminal"
            ],

            "sea": [
                "port",
                "vessel",
                "ship",
                "canal",
                "ocean",
                "maritime",
                "dock"
            ],

            "rail": [
                "rail",
                "track",
                "locomotive",
                "station"
            ],

            "road": [
                "highway",
                "truck",
                "traffic",
                "bridge",
                "road",
                "delivery"
            ]
        }


    def apply_filter(
        self,
        semantic_score: float,
        news_context: str,
        transport_mode: str
    ) -> float:

        if semantic_score <= 0:
            return 0.0

        news_words = (
            news_context.lower().split()
        )

        if (
            transport_mode == "sea"
            and any(
                kw in news_words
                for kw in [
                    "port",
                    "vessel",
                    "canal",
                    "ocean",
                    "maritime"
                ]
            )
        ):

            if not any(
                kw in news_words
                for kw in [
                    "airport",
                    "flight"
                ]
            ):

                return 0.0

        if (
            transport_mode == "air"
            and any(
                kw in news_words
                for kw in [
                    "airport",
                    "flight"
                ]
            )
        ):

            if not any(
                kw in news_words
                for kw in [
                    "port",
                    "vessel",
                    "maritime"
                ]
            ):

                return 0.0

        return semantic_score


    def max_pool_threats(
        self,
        scores: List[float]
    ) -> float:

        return float(
            np.max(scores)
        ) if scores else 0.0