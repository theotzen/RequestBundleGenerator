# RequestClientGenerator

Map OpenAPI to a bundle to get simple internal requests.

Define your OpenAPI documentation URL, a path of where to generate the bundle, and run 

`python3 path/to/package/main.py '<base_url/OpenAPI/docs>>' '/path/to/generate/req_bundles <async|sync>'
`

Each define request in OpenAPI will generate an async HTTP call function designed to hit the related endpoint from another service. 

## Example 
A GET endpoint defined in a FastAPI router like :
```
@router.get(path="/endpont/{item_id}")
async def get_item(item_id: str, user_id: str = Depends(oauth2.require_user)):
    # your logic
    return {"item": itemResponseEntity(item)}
```
will generate an async HTTP call function : 
```
async def get_item(item_id: str, cookies: dict = None, base_url: str = base_url, endpoint: str = '/endpont/{item_id}`'):
	try: 
		res = await client.get(url=base_url+endpoint+ '/'+item_id) 
        if res.status_code >= 300:
            raise HTTPException(status_code=res.status_code, detail=res.json()['detail'])
	except httpx.HTTPError as err: 
		raise SystemExit(err)
	return res.json()
```
that can then be used in another service to request data :
```
@router.get(path='/OtherServiceEndpoint',
            status_code=status.HTTP_200_OK)
async def other_service_endpoint():
    item = await get_item()
    return item
```