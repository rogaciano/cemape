"""
Serviço de validação de certificados digitais ICP-Brasil (e-CPF A1).

Extrai CPF e dados do titular a partir de arquivo .pfx.
Suporta os padrões:
  - CN no formato "NOME PESSOA:CPF:12345678901" (maioria das ACs)
  - SubjectAltName OtherName OID 2.16.76.1.3.1 (padrão DOC-ICP-04)
"""
import re
import datetime

from cryptography import x509
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.serialization import pkcs12
from cryptography.x509.oid import NameOID


# OID ICP-Brasil para e-CPF — DOC-ICP-04
OID_ICP_BRASIL_CPF = "2.16.76.1.3.1"


def validar_pfx(pfx_bytes: bytes, senha: str) -> dict:
    """
    Valida um arquivo .pfx e extrai dados do certificado ICP-Brasil.

    Args:
        pfx_bytes: conteúdo binário do arquivo .pfx
        senha: senha de proteção do arquivo

    Returns:
        dict com chaves: cpf, nome, valido_ate, emissor

    Raises:
        ValueError: certificado inválido, expirado, senha errada ou CPF não encontrado
    """
    try:
        senha_bytes = senha.encode('utf-8') if senha else b''
        private_key, cert, chain = pkcs12.load_key_and_certificates(
            pfx_bytes, senha_bytes, default_backend()
        )
    except Exception:
        raise ValueError(
            "Não foi possível abrir o certificado. "
            "Verifique se o arquivo é um .pfx válido e se a senha está correta."
        )

    if cert is None:
        raise ValueError("O arquivo não contém um certificado.")

    # Verificar período de validade
    agora = datetime.datetime.now(datetime.timezone.utc)
    if cert.not_valid_before_utc > agora:
        raise ValueError("Certificado ainda não está dentro do prazo de validade.")
    if cert.not_valid_after_utc < agora:
        raise ValueError(
            f"Certificado expirado em "
            f"{cert.not_valid_after_utc.strftime('%d/%m/%Y')}."
        )

    cpf = _extrair_cpf(cert)
    if not cpf:
        raise ValueError(
            "CPF não encontrado no certificado. "
            "Certifique-se de que é um certificado e-CPF emitido por uma AC ICP-Brasil."
        )

    nome = _extrair_nome(cert)
    emissor = _extrair_emissor(cert)

    return {
        'cpf': cpf,
        'nome': nome,
        'valido_ate': cert.not_valid_after_utc,
        'emissor': emissor,
    }


# ---------------------------------------------------------------------------
# Helpers internos
# ---------------------------------------------------------------------------

def _extrair_cpf(cert: x509.Certificate) -> str | None:
    """Tenta extrair CPF do certificado usando múltiplas estratégias."""

    # Estratégia 1 — CN no formato "NOME:CPF:12345678901"
    cpf = _cpf_do_cn(cert)
    if cpf:
        return cpf

    # Estratégia 2 — SubjectAltName com OID ICP-Brasil 2.16.76.1.3.1
    cpf = _cpf_da_san(cert)
    if cpf:
        return cpf

    # Estratégia 3 — Busca por 11 dígitos válidos em qualquer campo do Subject
    cpf = _cpf_por_varredura(cert)
    return cpf


def _cpf_do_cn(cert: x509.Certificate) -> str | None:
    try:
        for attr in cert.subject.get_attributes_for_oid(NameOID.COMMON_NAME):
            # Formatos comuns: "FULANO DE TAL:00000000000:00000000000"
            # ou "FULANO DE TAL:CPF:00000000000"
            partes = attr.value.split(':')
            for parte in reversed(partes):
                candidate = re.sub(r'\D', '', parte)
                if len(candidate) == 11 and _validar_cpf(candidate):
                    return candidate
    except Exception:
        pass
    return None


def _cpf_da_san(cert: x509.Certificate) -> str | None:
    """
    Extrai CPF do SubjectAltName OtherName com OID 2.16.76.1.3.1.
    O valor codificado (DER) contém: [8 dígitos data nascimento][11 dígitos CPF][...]
    """
    try:
        san_ext = cert.extensions.get_extension_for_class(x509.SubjectAlternativeName)
        for name in san_ext.value:
            if isinstance(name, x509.OtherName):
                if name.type_id.dotted_string == OID_ICP_BRASIL_CPF:
                    # Decodifica o valor: ignora bytes ASN.1 e extrai sequências numéricas
                    raw = name.value
                    # Tenta decodificar como ASCII/UTF-8 e buscar CPF
                    try:
                        texto = raw.decode('ascii', errors='replace')
                    except Exception:
                        texto = ''
                    # Procura 11 dígitos consecutivos válidos
                    for m in re.finditer(r'\d{11}', texto):
                        candidate = m.group(0)
                        if _validar_cpf(candidate):
                            return candidate
                    # Fallback: extrai bytes numéricos direto
                    apenas_nums = re.sub(rb'\D', b'', raw)
                    if len(apenas_nums) >= 11:
                        candidate = apenas_nums[8:19].decode('ascii', errors='replace')
                        if len(candidate) == 11 and _validar_cpf(candidate):
                            return candidate
    except Exception:
        pass
    return None


def _cpf_por_varredura(cert: x509.Certificate) -> str | None:
    """Varre todos os campos do Subject procurando 11 dígitos que sejam um CPF válido."""
    try:
        for attr in cert.subject:
            for m in re.finditer(r'\d{11}', attr.value):
                candidate = m.group(0)
                if _validar_cpf(candidate):
                    return candidate
    except Exception:
        pass
    return None


def _extrair_nome(cert: x509.Certificate) -> str:
    try:
        cns = cert.subject.get_attributes_for_oid(NameOID.COMMON_NAME)
        if cns:
            # Remove sufixo ":CPF:00000000000" se presente
            nome = re.sub(r':.*$', '', cns[0].value).strip()
            return nome
    except Exception:
        pass
    return ''


def _extrair_emissor(cert: x509.Certificate) -> str:
    try:
        orgs = cert.issuer.get_attributes_for_oid(NameOID.ORGANIZATION_NAME)
        if orgs:
            return orgs[0].value
        cns = cert.issuer.get_attributes_for_oid(NameOID.COMMON_NAME)
        if cns:
            return cns[0].value
    except Exception:
        pass
    return 'Desconhecido'


def _validar_cpf(cpf: str) -> bool:
    """Valida CPF pelos dígitos verificadores."""
    if len(cpf) != 11 or cpf == cpf[0] * 11:
        return False
    # Primeiro dígito verificador
    soma = sum(int(cpf[i]) * (10 - i) for i in range(9))
    d1 = (soma * 10 % 11) % 10
    if d1 != int(cpf[9]):
        return False
    # Segundo dígito verificador
    soma = sum(int(cpf[i]) * (11 - i) for i in range(10))
    d2 = (soma * 10 % 11) % 10
    return d2 == int(cpf[10])
