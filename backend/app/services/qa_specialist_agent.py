from app.services.rules.qa_nulls import check_nulls
from app.services.rules.qa_duplicates import check_duplicates
from app.services.rules.qa_data_types import check_data_types
from app.services.rules.qa_outliers import check_outliers_iqr
from app.services.rules.qa_balance import check_balance

class QASpecialistAgent:
    """
    Agente Especialista QA.
    Recibe un DataFrame y un test concreto, lo ejecuta y devuelve el resultado.
    El orquestador le delega la ejecución de las reglas.
    """

    AVAILABLE_TESTS = {
        "nulls":      check_nulls,
        "duplicates": check_duplicates,
        "data_types": check_data_types,
        "outliers":   check_outliers_iqr,
        "balance":    check_balance,
    }

    def run_test(self, test_name: str, df, critical_columns: list = []):
        """
        Ejecuta un único test sobre el DataFrame.
        Devuelve el resultado enriquecido con el nombre y el resumen.
        """
        if test_name not in self.AVAILABLE_TESTS:
            return None

        test_fn = self.AVAILABLE_TESTS[test_name]
        result = test_fn(df)
        result["critical_columns"] = critical_columns

        summary = self._build_summary(test_name, result)

        return {
            "name": test_name,
            "status": result.get("status", "unknown"),
            "summary": summary,
            "metrics": result,
            "recommendations": result.get("recommendations", [])
        }

    def _build_summary(self, test_name: str, result: dict) -> str:
        if test_name == "nulls":
            return (
                f"{len(result.get('critical', []))} críticos, "
                f"{len(result.get('warnings', []))} avisos"
            )
        if test_name == "duplicates":
            return (
                f"{len(result.get('critical', []))} críticos, "
                f"{len(result.get('warnings', []))} duplicados"
            )
        if test_name == "data_types":
            return f"{len(result.get('mismatches', []))} columnas con tipos inesperados"
        if test_name == "outliers":
            total = result.get("metrics", {}).get("total_outliers", 0)
            return f"{total} outliers detectados"
        if test_name == "balance":
            ratio = (
                result.get("metrics", {})
                .get("majority_class_ratio", 0)
            )
            return (
                f"Clase mayoritaria: {round(ratio * 100, 2)}%"
            )
        return ""