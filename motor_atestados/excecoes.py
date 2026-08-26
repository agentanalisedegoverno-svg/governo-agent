"""Excecoes de dominio convertidas em respostas previsiveis pela API."""


class ErroMotor(ValueError):
    codigo = "erro_motor"


class DocumentoInvalido(ErroMotor):
    codigo = "documento_invalido"


class OcrNecessario(ErroMotor):
    codigo = "ocr_necessario"


class ConhecimentoInvalido(ErroMotor):
    codigo = "conhecimento_invalido"


class ProvedorIndisponivel(ErroMotor):
    codigo = "provedor_indisponivel"
