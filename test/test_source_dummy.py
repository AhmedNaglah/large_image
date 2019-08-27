# -*- coding: utf-8 -*-

from large_image import getTileSource
import large_image_source_dummy


def testDummyTileSource():
    source = large_image_source_dummy.DummyTileSource()
    tileMetadata = source.getMetadata()
    assert tileMetadata['tileWidth'] == 0
    assert tileMetadata['tileHeight'] == 0
    assert tileMetadata['sizeX'] == 0
    assert tileMetadata['sizeY'] == 0
    assert tileMetadata['levels'] == 0
    assert tileMetadata['magnification'] is None
    assert tileMetadata['mm_x'] is None
    assert tileMetadata['mm_y'] is None
    assert source.getTile(0, 0, 0) == b''


def testGetDummyTileSource():
    source = getTileSource('large_image://dummy')
    assert isinstance(source, large_image_source_dummy.DummyTileSource)
