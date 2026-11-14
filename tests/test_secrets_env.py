from app.core.secrets_env import export_to_environ


def test_exporta_texto_e_numeros_como_texto():
    environ = {}
    names = export_to_environ({"DATABASE_URL": "postgresql://x", "LLM_DELAY_SECONDS": 4}, environ)
    assert environ == {"DATABASE_URL": "postgresql://x", "LLM_DELAY_SECONDS": "4"}
    assert names == ["DATABASE_URL", "LLM_DELAY_SECONDS"]


def test_ignora_tabelas_booleanos_e_listas():
    environ = {}
    export_to_environ({"auth": {"client_id": "x"}, "FLAG": True, "LISTA": [1, 2]}, environ)
    assert environ == {}


def test_nao_sobrescreve_variavel_existente():
    environ = {"DATABASE_URL": "do-ambiente"}
    names = export_to_environ({"DATABASE_URL": "do-secret"}, environ)
    assert environ["DATABASE_URL"] == "do-ambiente" and names == []


def test_devolve_apenas_nomes_nunca_valores():
    names = export_to_environ({"REVISORES": "senha-secreta"}, {})
    assert names == ["REVISORES"] and "senha-secreta" not in repr(names)