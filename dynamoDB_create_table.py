import boto3
# Get the service resource.
import key_config as keys

dynamodb = boto3.resource('dynamodb',
                          aws_access_key_id=keys.ACCESS_KEY,
                          aws_secret_access_key=keys.SECRET_KEY,
                          region_name=keys.REGION_NAME
                          )


# Create the DynamoDB table.
table = dynamodb.create_table(
    TableName='User',
    KeySchema=[
        {
            'AttributeName': 'email',
            'KeyType': 'HASH'
        }

    ],
    AttributeDefinitions=[
             {
            'AttributeName': 'email',
            'AttributeType': 'S'
        }
    ],
    ProvisionedThroughput={
        'ReadCapacityUnits': 5,
        'WriteCapacityUnits': 5
    }
)

# Wait until the table exists.
table.meta.client.get_waiter('table_exists').wait(TableName='User')

# Print out some data about the table.
print(table.item_count)

def CreatATableBook():
    # dynamodb.list_tables()
    dynamodb.create_table(
        TableName='Log',  # Name of the table
        AttributeDefinitions=[  # Name and type of the attributes
            {
                'AttributeName': 'file',  # Name of the attribute
                'AttributeType': 'S'  # N -> Number (S -> String, B-> Binary)
            }
        ],

        KeySchema=[  # Partition key/sort key attribute
            {
                'AttributeName': 'file',
                'KeyType': 'HASH'
                # 'HASH' -> partition key, 'RANGE' -> sort key
            }
        ],
        ProvisionedThroughput={
             'ReadCapacityUnits': 5,
             'WriteCapacityUnits': 5
        }

    )

CreatATableBook()

