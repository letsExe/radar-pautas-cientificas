import pytest

from app.services.validation_service import MAX_COMMENT_CHARS, ValidationError, ValidationService

ANALYSIS_ID = "0b6b1f3e-5a5e-4f0e-9d58-2f3f7a1c9c11"


class FakeRepository:
    def __init__(self, exists=True):
        self.exists = exists
        self.saved = []

    def analysis_exists(self, analysis_id):
        return self.exists

    def save(self, analysis_id, reviewer_name, agrees, comment):
        self.saved.append((analysis_id, reviewer_name, agrees, comment))


def test_grava_com_nome_e_comentario_normalizados():
    repository = FakeRepository()
    ValidationService(repository).submit(ANALYSIS_ID, "  Ana   Souza ", True, "  boa pauta  ")
    [(analysis_id, reviewer, agrees, comment)] = repository.saved
    assert str(analysis_id) == ANALYSIS_ID
    assert (reviewer, agrees, comment) == ("Ana Souza", True, "boa pauta")


def test_comentario_vazio_vira_none():
    repository = FakeRepository()
    ValidationService(repository).submit(ANALYSIS_ID, "Ana", False, "   ")
    assert repository.saved[0][3] is None


def test_recusa_nome_vazio():
    repository = FakeRepository()
    with pytest.raises(ValidationError):
        ValidationService(repository).submit(ANALYSIS_ID, "  ", True)
    assert repository.saved == []


def test_recusa_revisor_fora_da_lista():
    repository = FakeRepository()
    service = ValidationService(repository, allowed_reviewers=["Ana", "Bruno"])
    with pytest.raises(ValidationError):
        service.submit(ANALYSIS_ID, "Carlos", True)
    service.submit(ANALYSIS_ID, "Bruno", True)
    assert len(repository.saved) == 1


def test_recusa_comentario_muito_longo():
    with pytest.raises(ValidationError):
        ValidationService(FakeRepository()).submit(ANALYSIS_ID, "Ana", True, "x" * (MAX_COMMENT_CHARS + 1))


def test_recusa_analise_inexistente_e_id_invalido():
    repository = FakeRepository(exists=False)
    with pytest.raises(ValidationError):
        ValidationService(repository).submit(ANALYSIS_ID, "Ana", True)
    with pytest.raises(ValidationError):
        ValidationService(FakeRepository()).submit("nao-e-uuid", "Ana", True)
    assert repository.saved == []