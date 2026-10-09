"""Content identities. Restricted JCS: numbers are encoded as decimal strings.

This deliberately rejects JSON numbers instead of approximating RFC 8785's
ECMAScript number serialization. Object keys use UTF-16 code unit ordering.
"""
import hashlib
import json

IDENTITY_VERSION = 'causal-identity-v1'


def canonical_bytes(value):
    def encode(item):
        if item is None or isinstance(item, bool):
            return json.dumps(item)
        if isinstance(item, str):
            try:
                item.encode('utf-8', errors='strict')
            except UnicodeError as exc:
                raise ValueError('Invalid Unicode in identity') from exc
            return json.dumps(item, ensure_ascii=False)
        if isinstance(item, list):
            return '[' + ','.join(encode(x) for x in item) + ']'
        if isinstance(item, dict):
            if any(not isinstance(k, str) for k in item):
                raise ValueError('Identity keys must be strings')
            for key in item:
                encode(key)
            keys = sorted(item, key=lambda k: k.encode('utf-16-be'))
            return '{' + ','.join(encode(k) + ':' + encode(item[k]) for k in keys) + '}'
        raise ValueError('Identity numbers must be canonical decimal strings')
    return encode(value).encode('utf-8')


def identity_document(value):
    """Convert generated integral counts to strings; never accept floats."""
    if isinstance(value, int) and not isinstance(value, bool):
        return str(value)
    if isinstance(value, list) or isinstance(value, tuple):
        return [identity_document(x) for x in value]
    if isinstance(value, dict):
        return {k: identity_document(v) for k, v in value.items()}
    return value


def content_hash(domain, document):
    if domain not in {'candidate', 'snapshot', 'questions', 'projection', 'evidence'}:
        raise ValueError('Unknown identity domain')
    prefix = f'jev:{domain}:{IDENTITY_VERSION}\n'.encode('ascii')
    return hashlib.sha256(prefix + canonical_bytes(document)).hexdigest()
