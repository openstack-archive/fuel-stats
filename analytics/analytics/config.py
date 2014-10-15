INDEX_FUEL = 'fuel'
DOC_TYPE_INSTALLATION = 'installation'

INDEXES_MAPPINGS = {
    INDEX_FUEL: {
        DOC_TYPE_INSTALLATION: {
            'properties': {
                'aid': {'type': 'string', 'index': 'not_analyzed'},
                'clusters': {
                    'type': 'nested',
                    'properties': {
                        'release': {
                            'type': 'nested',
                            'properties': {
                                'version': {'type': 'string', 'index': 'not_analyzed'},
                                'os': {'type': 'string', 'index': 'not_analyzed'},
                                'name': {'type': 'string', 'index': 'not_analyzed'}
                            }
                        },
                        # 'os': {'type': 'string'},
                        'nodes': {
                            'type': 'object'
                        }
                    }
                }
            }
        }
    }
}
