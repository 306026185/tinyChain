


from tinychain.db.tiny_vector_database import TinyVectorDatabaseClient
from tinychain.db.models import Rec

if __name__ == "__main__":
    tiny_client = TinyVectorDatabaseClient("tiny_db")

    collection = tiny_client.create_collection(collection_name="my_collection")

    collection.add(documents=[
        "This is a document about pineapple",
        "This is a document about oranges"
    ],ids=["id5","id6"],namespace="test2")

    res = collection.query(Rec(
        rec_id="id3",
        namespace="test1",
        document="This is a query document about hawaii",
        create_at="0204-05-12",
        embedding="",
        is_used=True
    ),n_result=2)

    collection.query_result_rank(res)

    exit(0)

    rec_one = Rec(
        rec_id="id1",
        namespace="test1",
        document="This is a document about pineapple",
        create_at="0204-05-12",
        embedding="",
        is_used=True
    )
    # collection.add_rec(rec_one)

    rec_two = Rec(
        rec_id="id2",
        namespace="test1",
        document="This is a document about oranges",
        create_at="0204-05-12",
        embedding="",
        is_used=True
    )

    # collection.add_rec(rec_two)
    # collection.add(
    #     documents=[
    #         "This is a document about pineapple",
    #         "This is a document about oranges"
    #     ],
    #     ids=["id1", "id2"]
    # )
