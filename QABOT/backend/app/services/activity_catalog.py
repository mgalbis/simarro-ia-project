from app.schemas.quality_assessment import ActivityType


DEFAULT_TESTS_BY_ACTIVITY = {
    ActivityType.MINABLE_DATASET_VALIDATION: [
        "nulls",
        "duplicates",
        "data_types",
        "outliers",
        "balance",
        "skewness",
    ],
    ActivityType.DATASET_SPLIT_VALIDATION: [
        "dataset_split",
    ],
    ActivityType.DATASET_SPLIT_VALIDATION_3DS: [
        "dataset_train",
        "dataset_validation",
        "dataset_test",
        "minable_dataset",
    ],
    ActivityType.MODEL_PERFORMANCE_EVALUATION: [
        "model_performance",
    ],
    ActivityType.THRESHOLD_QUALITY_EVALUATION: [
        "model_performance",
    ],
}


REQUIRED_ARTIFACTS_BY_ACTIVITY = {
    ActivityType.MINABLE_DATASET_VALIDATION: [
        "dataset",
    ],
    ActivityType.DATASET_SPLIT_VALIDATION: [
        "dataset_with_split_column",
        "split_column",
    ],
    ActivityType.DATASET_SPLIT_VALIDATION_3DS: [
        "dataset_train",
        "dataset_validation",
        "dataset_test",
        "minable_dataset",
    ],
    ActivityType.MODEL_PERFORMANCE_EVALUATION: [
        "test_dataset",
        "target_column",
        "prediction_or_score_column",
    ],
    ActivityType.THRESHOLD_QUALITY_EVALUATION: [
        "dataset_with_scores",
        "target_column",
        "score_column",
        "current_threshold",
    ],
}


ACTIVITY_OBJECTIVES = {
    ActivityType.MINABLE_DATASET_VALIDATION: (
        "Evaluate the structural and basic quality of a minable dataset without modifying it."
    ),
    ActivityType.DATASET_SPLIT_VALIDATION: (
        "Evaluate train, validation and test partition quality without creating or modifying partitions."
    ),
    ActivityType.MODEL_PERFORMANCE_EVALUATION: (
        "Evaluate model performance using provided labels and predictions or scores without modifying any artifact."
    ),
    ActivityType.THRESHOLD_QUALITY_EVALUATION: (
        "Evaluate the diagnostic behaviour of the current classification threshold without updating it."
    ),
}