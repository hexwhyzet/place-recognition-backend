#echo "Enter yandex registry id:"
#read -r yandex_registry_id
cd ../../
echo "Enter image tag:"
read -r image_tag
docker build -t place-recognition-mining-worker -f miner/worker/Dockerfile .
docker tag place-recognition-mining-worker "cr.yandex/crpktc7jeim3h82e69hv/place-recognition-mining-worker:$image_tag"
docker push "cr.yandex/crpktc7jeim3h82e69hv/place-recognition-mining-worker:$image_tag"
