#!/usr/bin/env python3
"""Focused regression proof for Spanish scanning and draft publication safety."""
import importlib.util
from pathlib import Path
from tempfile import TemporaryDirectory
import json
import sys

ROOT=Path(__file__).resolve().parent.parent
sys.path.insert(0,str(ROOT/'scripts'))
from validate_es_text import text_findings, PageText

def load_builder():
    spec=importlib.util.spec_from_file_location('build_essays',ROOT/'build_essays.py')
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module

def main():
    assert not text_findings('¿Qué ocurre? Pero ¿quién lo sabe? Consciencia y conciencia.', 'fixture')
    assert len(text_findings('¿Qué ocurre? Quién lo sabe?', 'fixture'))==1
    assert {x['rule'] for x in text_findings('No solo lee, sino que escribe. No sólo. —', 'fixture')}=={'no_solo_sino','no_solo_accent','em_dash'}
    assert not text_findings('«What Is It Like to Be a Bat?»', 'fixture')
    assert not text_findings('—Hola —dice ella—.\n—¿Qué tal?', 'fixture', allow_dialogue=True)
    assert text_findings('Una frase —un inciso—.', 'fixture', allow_dialogue=True)
    page=PageText('<html lang="es"><script>what?</script><div class="essay-body"><p>¿Qué ocurre?</p><div>Otra frase.</div></div><footer>Pie</footer></html>')
    assert 'what?' not in ''.join(page.parts) and 'Pie' not in ''.join(page.body)
    b=load_builder()
    with TemporaryDirectory() as tmp:
        tmp=Path(tmp);b.OUTPUT_DIR=tmp/'essays';b.OUTPUT_DIR.mkdir()
        b.DATA_DIR=tmp/'data';b.DATA_DIR.mkdir();(b.DATA_DIR/'essays.json').write_text('[]')
        source=tmp/'fixture.md'
        front='''---
id: fixture
lang: es
slug: fixture-es
title: "Una prueba"
subtitle: "Una descripción."
date: 2026-09-24
author: Javier del Puerto
tags: [rights]
book: mindkind
translation: fixture-en
status: draft
excerpt: "Una descripción."
---
Texto de prueba.
'''
        source.write_text(front)
        output=b.OUTPUT_DIR/'fixture-es.html';output.write_text('LIVE ORIGINAL')
        assert b.build_essay(source) is None
        assert output.read_text()=='LIVE ORIGINAL'
        assert (b.DATA_DIR/'essays.json').read_text()=='[]'
        # Same complete front matter publishes only after explicit status change.
        source.write_text(front.replace('status: draft','status: published'))
        import shutil
        shutil.copytree(ROOT/'data/i18n', b.DATA_DIR/'i18n')
        shutil.copyfile(ROOT/'data/books.json', b.DATA_DIR/'books.json')
        result=b.build_essay(source)
        assert result['slug']=={'es':'fixture-es'}
        assert 'fixture-en' in output.read_text() and 'Una prueba' in output.read_text()
        assert 'septiembre de 2026' in output.read_text()
        assert 'examines how' not in output.read_text()
        assert 'explora qué sucede' in output.read_text()
        # New Spanish source must not turn English related links into Spanish.
        b.CONTENT_DIR=tmp/'content';b.CONTENT_DIR.mkdir()
        entry={'id':'fixture','slug':{'en':'fixture-en'},'title':{'en':'English title'},'status':'published'}
        (b.DATA_DIR/'essays.json').write_text(json.dumps([entry]))
        (b.CONTENT_DIR/'fixture-es.md').write_text(source.read_text())
        loaded=b.load_all_essays_metadata()
        assert loaded['fixture']['slug']=={'en':'fixture-en','es':'fixture-es'}
        assert loaded['fixture']['title']=={'en':'English title','es':'Una prueba'}
        assert loaded['fixture-en']==loaded['fixture-es']

    print('Spanish scanner and draft/publication regression checks PASS')

if __name__=='__main__': main()
