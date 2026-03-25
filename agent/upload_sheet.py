import os
import json
import gspread
from typing import Dict, List, Any, Optional
from datetime import datetime
from google.auth.exceptions import RefreshError


def authenticate_gspread() -> Optional[gspread.Client]:
    """
    gspread를 사용하여 Google Sheets에 인증합니다.
    
    Returns:
        gspread.Client: 인증된 gspread 클라이언트 또는 None
    """
    try:
        # Service Account 키 파일이 있으면 우선 사용
        if os.path.exists('service_account.json'):
            gc = gspread.service_account(filename='service_account.json')
            print("Service Account로 인증되었습니다.")
            return gc
        
        # OAuth credentials.json 파일 사용
        if os.path.exists('credentials.json'):
            gc = gspread.oauth(
                credentials_filename='credentials.json',
                authorized_user_filename='token.json'
            )
            print("OAuth로 인증되었습니다.")
            return gc
        
        print("Error: 인증 파일이 필요합니다.")
        print("- Service Account: service_account.json")
        print("- 또는 OAuth: credentials.json")
        return None
        
    except Exception as e:
        print(f"gspread 인증 실패: {e}")
        return None


def prepare_sheet_data(analysis_results: List[Dict[str, Any]]) -> List[List[Any]]:
    """
    분석 결과를 Google Sheets에 맞는 2D 배열 형태로 변환합니다.
    
    Args:
        analysis_results: 분석 결과 딕셔너리 리스트
    
    Returns:
        2D 배열 형태의 데이터
    """
    # 헤더 행
    headers = [
        'Company Name', 'Location', 'Phone', 'Website', 'Rating', 'Total Reviews',
        'Services', 'Target Properties', 'Company Size', 'Specializations',
        'Contact Emails', 'Contact Phones', 'Contact Addresses',
        'Key Features', 'Summary', 'Analysis Date'
    ]
    
    data = [headers]
    
    for result in analysis_results:
        # 기본 회사 정보
        company_name = result.get('name', 'Unknown')
        location = f"{result.get('city', '')}, {result.get('state', '')}"
        phone = result.get('phone_number', '')
        website = result.get('website', '')
        rating = result.get('rating', '')
        total_reviews = result.get('user_ratings_total', '')
        
        # 분석된 정보
        analysis = result.get('analysis', {})
        services = ', '.join(analysis.get('services', []))
        target_properties = ', '.join(analysis.get('target_properties', []))
        company_size = analysis.get('company_size', '')
        specializations = ', '.join(analysis.get('specializations', []))
        
        contact_info = analysis.get('contact_info', {})
        contact_emails = ', '.join(contact_info.get('emails', []))
        contact_phones = ', '.join(contact_info.get('phones', []))
        contact_addresses = ', '.join(contact_info.get('addresses', []))
        
        key_features = ', '.join(analysis.get('key_features', []))
        summary = analysis.get('summary', '')
        
        analysis_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        row = [
            company_name, location, phone, website, rating, total_reviews,
            services, target_properties, company_size, specializations,
            contact_emails, contact_phones, contact_addresses,
            key_features, summary, analysis_date
        ]
        
        data.append(row)
    
    return data


def format_sheet(worksheet):
    """
    시트의 헤더 행을 포맷팅합니다.
    
    Args:
        worksheet: gspread 워크시트 객체
    """
    try:
        # 헤더 행 스타일 설정
        worksheet.format('1:1', {
            'backgroundColor': {'red': 0.9, 'green': 0.9, 'blue': 0.9},
            'textFormat': {'bold': True},
            'horizontalAlignment': 'CENTER'
        })
        
        # 열 너비 자동 조정 (gspread에서는 제한적이므로 수동 설정)
        worksheet.columns_auto_resize(0, len(worksheet.row_values(1)))
        
    except Exception as e:
        print(f"시트 포맷팅 중 오류: {e}")


def upload_to_google_sheets(
    analysis_results: List[Dict[str, Any]], 
    sheet_title: Optional[str] = None,
    spreadsheet_id: Optional[str] = None,
    worksheet_name: str = "Sheet1"
) -> Optional[str]:
    """
    분석 결과를 Google Sheets에 업로드합니다.
    
    Args:
        analysis_results: 분석 결과 딕셔너리 리스트
        sheet_title: 스프레드시트 제목 (새로 생성할 경우)
        spreadsheet_id: 기존 스프레드시트 ID (기존 시트에 추가할 경우)
        worksheet_name: 워크시트 이름 (기본값: "Sheet1")
    
    Returns:
        spreadsheet_id: 업로드된 스프레드시트 ID 또는 None
    """
    if not analysis_results:
        print("업로드할 분석 결과가 없습니다.")
        return None
    
    # gspread 인증
    gc = authenticate_gspread()
    if not gc:
        return None
    
    try:
        # 새 스프레드시트 생성 또는 기존 스프레드시트 사용
        if not spreadsheet_id:
            if not sheet_title:
                sheet_title = f"Property Management Lead Analysis - {datetime.now().strftime('%Y-%m-%d %H:%M')}"
            
            # 새 스프레드시트 생성
            spreadsheet = gc.create(sheet_title)
            spreadsheet_id = spreadsheet.id
            worksheet = spreadsheet.sheet1
            
            print(f"새 스프레드시트가 생성되었습니다: {sheet_title}")
            print(f"스프레드시트 ID: {spreadsheet_id}")
            
        else:
            # 기존 스프레드시트 열기
            spreadsheet = gc.open_by_key(spreadsheet_id)
            
            # 워크시트 선택 또는 생성
            try:
                worksheet = spreadsheet.worksheet(worksheet_name)
            except gspread.WorksheetNotFound:
                worksheet = spreadsheet.add_worksheet(title=worksheet_name, rows=1000, cols=20)
                print(f"새 워크시트 '{worksheet_name}'가 생성되었습니다.")
        
        # 데이터 준비
        sheet_data = prepare_sheet_data(analysis_results)
        
        # 기존 데이터 확인
        existing_data = worksheet.get_all_values()
        
        if existing_data:
            # 기존 데이터가 있으면 새 데이터 추가 (헤더 제외)
            start_row = len(existing_data) + 1
            new_data = sheet_data[1:]  # 헤더 제외
            
            if new_data:
                # 데이터 범위 계산
                end_row = start_row + len(new_data) - 1
                end_col = chr(65 + len(new_data[0]) - 1)  # A, B, C... 
                range_name = f'A{start_row}:{end_col}{end_row}'
                
                worksheet.update(range_name, new_data)
                print(f"{len(new_data)}개의 새 레코드가 추가되었습니다 (행 {start_row}-{end_row})")
        else:
            # 새 시트에 전체 데이터 입력 (헤더 포함)
            worksheet.update('A1', sheet_data)
            print(f"{len(sheet_data)-1}개의 레코드가 업로드되었습니다.")
            
            # 헤더 포맷팅 적용
            format_sheet(worksheet)
        
        # 스프레드시트 링크 출력
        print(f"Google Sheets 링크: https://docs.google.com/spreadsheets/d/{spreadsheet_id}")
        
        return spreadsheet_id
        
    except gspread.SpreadsheetNotFound:
        print(f"스프레드시트를 찾을 수 없습니다: {spreadsheet_id}")
        return None
    except Exception as e:
        print(f"데이터 업로드 실패: {e}")
        return None


def share_spreadsheet(spreadsheet_id: str, email: str, role: str = 'writer') -> bool:
    """
    스프레드시트를 특정 사용자와 공유합니다.
    
    Args:
        spreadsheet_id: 스프레드시트 ID
        email: 공유할 사용자 이메일
        role: 권한 ('owner', 'writer', 'reader')
    
    Returns:
        bool: 공유 성공 여부
    """
    try:
        gc = authenticate_gspread()
        if not gc:
            return False
        
        spreadsheet = gc.open_by_key(spreadsheet_id)
        spreadsheet.share(email, perm_type='user', role=role)
        print(f"스프레드시트가 {email}에게 {role} 권한으로 공유되었습니다.")
        return True
        
    except Exception as e:
        print(f"공유 실패: {e}")
        return False


def upload_analysis_results_to_sheets(
    analysis_results: List[Dict[str, Any]], 
    sheet_title: Optional[str] = None,
    share_with: Optional[str] = None
) -> Optional[str]:
    """
    분석 결과를 Google Sheets에 업로드하는 메인 함수입니다.
    
    Args:
        analysis_results: 분석 결과 딕셔너리 리스트
        sheet_title: 스프레드시트 제목 (선택사항)
        share_with: 공유할 이메일 주소 (선택사항)
    
    Returns:
        spreadsheet_id: 업로드된 스프레드시트 ID 또는 None
    
    Example:
        # 분석 결과 예시
        results = [
            {
                'name': 'ABC Property Management',
                'city': 'Austin',
                'state': 'TX',
                'phone_number': '+1 512-123-4567',
                'website': 'https://abcpm.com',
                'rating': 4.5,
                'user_ratings_total': 150,
                'analysis': {
                    'services': ['Residential Property Management', 'Tenant Screening'],
                    'contact_info': {
                        'emails': ['info@abcpm.com'],
                        'phones': ['+1 512-123-4567'],
                        'addresses': ['123 Main St, Austin, TX']
                    },
                    'key_features': ['24/7 Emergency Support', 'Online Portal'],
                    'target_properties': ['Single Family Homes', 'Condos'],
                    'company_size': 'medium',
                    'specializations': ['Luxury Properties'],
                    'summary': 'Professional property management company serving Austin area.'
                }
            }
        ]
        
        # Google Sheets에 업로드
        spreadsheet_id = upload_analysis_results_to_sheets(
            results, 
            "My Property Management Leads",
            "partner@example.com"  # 선택사항: 공유할 이메일
        )
    """
    spreadsheet_id = upload_to_google_sheets(analysis_results, sheet_title)
    
    # 공유 설정 (선택사항)
    if spreadsheet_id and share_with:
        share_spreadsheet(spreadsheet_id, share_with)
    
    return spreadsheet_id


def add_to_existing_sheet(
    analysis_results: List[Dict[str, Any]], 
    spreadsheet_id: str,
    worksheet_name: str = "Sheet1"
) -> bool:
    """
    기존 스프레드시트에 새 데이터를 추가합니다.
    
    Args:
        analysis_results: 분석 결과 딕셔너리 리스트
        spreadsheet_id: 기존 스프레드시트 ID
        worksheet_name: 워크시트 이름
    
    Returns:
        bool: 성공 여부
    """
    result = upload_to_google_sheets(
        analysis_results, 
        spreadsheet_id=spreadsheet_id,
        worksheet_name=worksheet_name
    )
    return result is not None


if __name__ == "__main__":
    # 테스트용 예시 데이터
    test_data = [
        {
            'name': 'CloverLeaf Property Management',
            'city': 'San Antonio', 
            'state': 'TX',
            'phone_number': '+1 210-827-7777',
            'website': 'http://www.cloverleafpropertymanagement.com/',
            'rating': 4.9,
            'user_ratings_total': 521,
            'analysis': {
                'services': ['Residential Property Management', 'Tenant Screening', 'Maintenance Services'],
                'contact_info': {
                    'emails': ['info@cloverleafpm.com'],
                    'phones': ['+1 210-827-7777'],
                    'addresses': ['8620 N New Braunfels Ave # 620, San Antonio, TX 78217']
                },
                'key_features': ['24/7 Emergency Support', 'Online Portal', 'Professional Staff'],
                'target_properties': ['Single Family Homes', 'Condos', 'Townhomes'],
                'company_size': 'medium',
                'specializations': ['Residential Properties'],
                'summary': 'Professional property management company serving San Antonio area with excellent reviews.'
            }
        }
    ]
    
    # 테스트 실행
    spreadsheet_id = upload_analysis_results_to_sheets(
        test_data, 
        "Test Property Management Analysis - gspread"
    )
    
    if spreadsheet_id:
        print(f"테스트 업로드 성공! 스프레드시트 ID: {spreadsheet_id}")
    else:
        print("테스트 업로드 실패")