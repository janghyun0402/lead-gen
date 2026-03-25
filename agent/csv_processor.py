import csv
import os
import json
from typing import List, Dict
import logging

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def process_csv_file(csv_file_path: str) -> List[Dict]:
    """
    Parse CSV file and extract organization data as dictionaries.
    
    Args:
        csv_file_path (str): Path to the CSV file
    
    Returns:
        List[Dict]: List of organization data dictionaries extracted from CSV rows
    """
    if not os.path.exists(csv_file_path):
        logger.error(f"CSV file not found: {csv_file_path}")
        return []
    
    organizations = []
    
    try:
        with open(csv_file_path, 'r', encoding='utf-8-sig') as file:
            # CSV 파일 읽기 (첫 번째 행을 헤더로 자동 감지)
            csv_reader = csv.DictReader(file)
            print(csv_reader.fieldnames)
            
            # 'Organization Name' 컬럼이 있는지 확인
            if 'Organization Name' not in csv_reader.fieldnames:
                logger.error("CSV file must contain 'Organization Name' column")
                return []
            
            logger.info(f"Found columns: {csv_reader.fieldnames}")
            
            # 각 행을 딕셔너리로 변환
            for row_num, row in enumerate(csv_reader, start=1):
                organization_name = row.get('Organization Name', '').strip()
                
                if not organization_name:
                    logger.warning(f"Row {row_num}: Empty organization name, skipping")
                    continue
                
                # 모든 컬럼 데이터를 포함하는 딕셔너리 생성
                
                # City, city 둘 다 인식할 수 있도록 처리
                city = None
                for key in row.keys():
                    if key.lower() == 'city':
                        city = row[key].strip()
                        break
                
                # 이름 주어진 경우는 이름도 추가
                first_name = None
                last_name = None
                for key in row.keys():
                    if key.lower() == 'first name':
                        first_name = row[key].strip()
                    if key.lower() == 'last name':
                        last_name = row[key].strip()
                        
                if first_name and last_name:
                    owner_name = f"{first_name} {last_name}"
                
                org_data = {
                    "row_number": row_num,
                    "organization_name": organization_name,
                    "city": city,
                    "owner_name": owner_name if owner_name else None,
                }
                
                # CSV의 다른 컬럼들도 포함
                for key, value in row.items():
                    if key not in ['Organization Name', 'City']:
                        org_data[key.lower().replace(' ', '_')] = value.strip() if value else None
                
                organizations.append(org_data)
                
                city_info = f" in {org_data['city']}" if org_data['city'] else ""
                logger.info(f"Extracted row {row_num}: {organization_name}{city_info}")
    
    except Exception as e:
        logger.error(f"Error reading CSV file: {e}")
        return []
    
    logger.info(f"Successfully extracted {len(organizations)} organizations from CSV file")
    return organizations




if __name__ == "__main__":
    # 테스트용 예제
    csv_file_path = "../csv_sample.csv"
    
    # CSV 파일 파싱 테스트
    organizations = process_csv_file(csv_file_path)
    
    if organizations:
        print(f"Successfully extracted {len(organizations)} organizations:")
        for org in organizations:
            print(f"  - {org['organization_name']}" + (f" in {org['city']}" if org['city'] else ""))
    else:
        print("No organizations extracted")
