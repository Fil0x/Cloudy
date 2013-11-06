import logger

from kamaki.clients import sendlog
from kamaki.clients.pithos import PithosClient
from kamaki.clients.storage import ClientError


class CloudyPithosClient(PithosClient):

    def upload_object(
            self, obj, f,
            size=None,
            hash_cb=None,
            upload_cb=None,
            etag=None,
            if_etag_match=None,
            if_not_exist=None,
            content_encoding=None,
            content_disposition=None,
            content_type=None,
            sharing=None,
            public=None,
            container_info_cache=None):
        self._assert_container()

        block_info = (
            blocksize, blockhash, size, nblocks) = self._get_file_block_info(
                f, size, container_info_cache)
        (hashes, hmap, offset) = ([], {}, 0)
        if not content_type:
            content_type = 'application/octet-stream'

        self._calculate_blocks_for_upload(
            *block_info,
            hashes=hashes,
            hmap=hmap,
            fileobj=f,
            hash_cb=hash_cb)

        hashmap = dict(bytes=size, hashes=hashes)
        missing, obj_headers = self._create_object_or_get_missing_hashes(
            obj, hashmap,
            content_type=content_type,
            size=size,
            if_etag_match=if_etag_match,
            if_etag_not_match='*' if if_not_exist else None,
            content_encoding=content_encoding,
            content_disposition=content_disposition,
            permissions=sharing,
            public=public)

        if missing is None:
            yield size
            return

        sendlog.info('%s blocks missing' % len(missing))
        for hash in missing:
            offset, bytes = hmap[hash]
            f.seek(offset)
            data = f.read(bytes)
            r = self._put_block(data, hash)
            yield bytes

        r = self.object_put(
            obj,
            format='json',
            hashmap=True,
            content_type=content_type,
            content_encoding=content_encoding,
            if_etag_match=if_etag_match,
            if_etag_not_match='*' if if_not_exist else None,
            etag=etag,
            json=hashmap,
            permissions=sharing,
            public=public,
            success=201)
