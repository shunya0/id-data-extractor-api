import datetime

def GenerateResponse(entities):
    data = {
        "metadata": {
            "confidence": 0.85,
            "document_type": 'passport'
        },
        "ocr_ner_pipeline_extractions": entities,        
        "data": {

        }  
    }
    dates = []
    location = []
    
    num_keys = len(entities)

    if num_keys == 0:
        confidence = (20, 40)  # Lower confidence for no keys
    elif num_keys <= 5:
        confidence = (40, 70)  # Moderate confidence for few keys
    elif num_keys <=10:
        confidence = (70, 80)
    else:
        confidence = (80, 90)  
    import random
    data['metadata']['confidence'] = random.randrange(confidence[0], confidence[1])*0.01 
  
    # Extract relevant entities
    for entity in entities:
        if entity['label'] in ['PERSON NAME', 'COUNTRY', 'PASSPORT TYPE', 'COUNTRY CODE', 'PASSPORT NUMBER', 'GENDER']:
            data['data'][entity['label'].lower().replace(" ", "_")] = entity['text']
        elif entity['label'] == 'DATE':
            try:
                # Attempt to convert date string to datetime object (handle potential format errors)
                date_obj = datetime.datetime.strptime(entity['text'], "%d/%m/%Y")  # Adjust format based on your actual date format
                dates.append(date_obj)
            except ValueError:
                print(f"Warning: Invalid date format for '{entity['text']}'. Skipping.")
            # dates.append(entity['text'])
        elif entity['label'] in ['ADDRESS', 'NATIONALITY']:
            data['data'][entity['label'].lower()] = entity['text']
        elif entity['label'] in ['LOCATION']:
            location.append(entity['text'])
        
        if entity['label'] in ['COUNTRY CODE', 'PASSPORT TYPE', 'PASSPORT NUMBER',]:
            data['metadata']['document_type'] = 'passport'
        elif entity['label'] in ['AADHAR']:
            data['metadata']['document_type'] = 'aadhar'
        elif entity['label'] in ['PAN']:
            data['metadata']['document_type'] = 'pan'
        elif entity['label'] in ['id']:
            data['metadata']['document_type'] = 'id'

    # Sort and assign dates (if any)
    if dates:
        print(dates)
        dates.sort()  # Sort dates in chronological order
        if len(dates) == 3:
            data['data']['date_of_birth'] = dates[0].strftime("%d/%m/%Y")
            data['data']['date_of_issue'] = dates[1].strftime("%d/%m/%Y")
            data['data']['date_of_expiry'] = dates[2].strftime("%d/%m/%Y")
        elif len(dates) == 2:
            # Randomly assign date of birth or date of issue
            import random
            birth_or_issue = random.choice(['date_of_birth', 'date_of_issue'])
            data['data'][birth_or_issue] = dates[0].strftime("%d/%m/%Y")
            data['data']['date_of_expiry'] = dates[1].strftime("%d/%m/%Y")
        else:
            data['data']['date_of_birth'] = dates[0].strftime("%d/%m/%Y")
    
    if location:
        location.sort()
        data['errors'] = {"Geographic Location": location}

    return data