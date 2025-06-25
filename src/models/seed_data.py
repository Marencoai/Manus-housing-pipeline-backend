from src.models.database import db, Project, Client, FundingSource, Application, TimeEntry
from src.models.database import ProjectPhase, FundingSourceType, ApplicationStatus
from datetime import datetime, date

def seed_database():
    """Seed the database with sample data including Dallas Mill Station project"""
    
    # Check if data already exists (with error handling for schema issues)
    try:
        if Project.query.first():
            return  # Data already seeded
    except Exception as e:
        # Database schema might not be fully created yet, continue with seeding
        print(f"Database schema check failed, proceeding with seeding: {e}")
        pass
    
    # Create Clients
    polk_cdc = Client(
        name="Polk County Community Development Corporation",
        organization="Polk CDC",
        email="info@polkcdc.org",
        phone="(503) 623-8173",
        address="1275 Lancaster Dr NE",
        city="Salem",
        state="Oregon",
        zip_code="97301",
        contact_person="Rita Bernardo"
    )
    
    gsa = Client(
        name="Geller, Silvis & Associates Inc.",
        organization="GS&A",
        email="info@gsaconsulting.com",
        phone="(503) 555-0123",
        address="123 Main St",
        city="Portland",
        state="Oregon",
        zip_code="97201",
        contact_person="Diana Marenco"
    )
    
    db.session.add_all([polk_cdc, gsa])
    db.session.commit()
    
    # Create Funding Sources
    funding_sources = [
        FundingSource(
            name="9% Low-Income Housing Tax Credit",
            type=FundingSourceType.LIHTC_9_PERCENT,
            agency="Oregon Housing and Community Services (OHCS)",
            description="Competitive 9% LIHTC program for affordable housing development",
            award_amount_min=500000,
            award_amount_max=5000000,
            requirements="New construction or substantial rehabilitation, minimum 30-year compliance period",
            website_url="https://www.oregon.gov/ohcs/development/Pages/LIHTC.aspx",
            is_active=True
        ),
        FundingSource(
            name="Federal Home Loan Bank AHP",
            type=FundingSourceType.FHLB_AHP,
            agency="Federal Home Loan Bank of Des Moines",
            description="Affordable Housing Program providing grants and subsidized loans",
            award_amount_min=100000,
            award_amount_max=2000000,
            requirements="Affordable housing for households at or below 80% AMI",
            website_url="https://www.fhlbdm.com/community-investment/ahp",
            is_active=True
        ),
        FundingSource(
            name="ORCA Predevelopment Loan Program",
            type=FundingSourceType.ORCA,
            agency="Oregon Residential and Community Action",
            description="Predevelopment loans for affordable housing projects",
            award_amount_min=50000,
            award_amount_max=500000,
            requirements="Predevelopment activities for affordable housing",
            website_url="https://orcaonline.org/",
            is_active=True
        ),
        FundingSource(
            name="HOME Investment Partnerships Program",
            type=FundingSourceType.HOME,
            agency="Oregon Housing and Community Services (OHCS)",
            description="Federal HOME funds for affordable housing development",
            award_amount_min=200000,
            award_amount_max=1500000,
            requirements="Affordable housing for households at or below 80% AMI",
            website_url="https://www.oregon.gov/ohcs/development/Pages/HOME.aspx",
            is_active=True
        ),
        FundingSource(
            name="Predevelopment Loan Program",
            type=FundingSourceType.PDLP,
            agency="Oregon Housing and Community Services (OHCS)",
            description="PDLP provides predevelopment loans for affordable housing",
            award_amount_min=25000,
            award_amount_max=300000,
            requirements="Predevelopment activities, must lead to permanent financing",
            website_url="https://www.oregon.gov/ohcs/development/Pages/PDLP.aspx",
            is_active=True
        ),
        FundingSource(
            name="Congressional Community Project Funding",
            type=FundingSourceType.CONGRESSIONAL_CIP,
            agency="U.S. Congress - Oregon Delegation",
            description="Federal appropriations through congressional representatives",
            award_amount_min=500000,
            award_amount_max=5000000,
            requirements="Community benefit, local support, detailed budget justification",
            website_url="https://www.wyden.senate.gov/",
            is_active=True
        )
    ]
    
    db.session.add_all(funding_sources)
    db.session.commit()
    
    # Create Projects
    dallas_mill = Project(
        name="Dallas Mill Station",
        address="179 & 188 SW Washington Street",
        city="Dallas",
        state="Oregon",
        zip_code="97338",
        phase=ProjectPhase.APPLICATION_FINANCING,
        project_type="New Construction",
        population_type="Family",
        housing_type="Multifamily",
        total_units=63,
        total_cost=25000000,
        funding_gap=2500000,
        client_id=polk_cdc.id,
        sharepoint_site_url="https://polkcdc.sharepoint.com/sites/DallasMillStation",
        sharepoint_email="dallasmill@polkcdc.org",
        sharepoint_group_id=None  # Will be populated when SharePoint site is created
    )
    
    sample_project = Project(
        name="Riverside Commons",
        address="456 River Road",
        city="Salem",
        state="Oregon",
        zip_code="97301",
        phase=ProjectPhase.PRE_DEVELOPMENT,
        project_type="Rehabilitation",
        population_type="Senior",
        housing_type="Multifamily",
        total_units=48,
        total_cost=18000000,
        funding_gap=1800000,
        client_id=polk_cdc.id,
        sharepoint_site_url="https://polkcdc.sharepoint.com/sites/RiversideCommons",
        sharepoint_email="riverside@polkcdc.org",
        sharepoint_group_id=None  # Will be populated when SharePoint site is created
    )
    
    db.session.add_all([dallas_mill, sample_project])
    db.session.commit()
    
    # Create Applications for Dallas Mill Station
    applications = [
        Application(
            project_id=dallas_mill.id,
            funding_source_id=funding_sources[0].id,  # 9% LIHTC
            status=ApplicationStatus.SUBMITTED,
            application_round="2023-5",
            requested_amount=2750000,
            submission_date=date(2023, 5, 1),
            notes="Primary funding source - 9% LIHTC competitive application",
            documents_folder="/sites/DallasMillStation/2023-5 LIHTC application"
        ),
        Application(
            project_id=dallas_mill.id,
            funding_source_id=funding_sources[1].id,  # FHLB AHP
            status=ApplicationStatus.APPROVED,
            application_round="2025",
            requested_amount=1200000,
            awarded_amount=1200000,
            submission_date=date(2025, 4, 15),
            decision_date=date(2025, 6, 1),
            notes="FHLB AHP funding approved - $1.2M award",
            documents_folder="/sites/DallasMillStation/FHLB AHP 2025"
        ),
        Application(
            project_id=dallas_mill.id,
            funding_source_id=funding_sources[4].id,  # PDLP
            status=ApplicationStatus.APPROVED,
            application_round="2024",
            requested_amount=150000,
            awarded_amount=150000,
            submission_date=date(2024, 1, 15),
            decision_date=date(2024, 2, 28),
            notes="PDLP funding executed - predevelopment loan secured",
            documents_folder="/sites/DallasMillStation/PDLP 2024"
        ),
        Application(
            project_id=dallas_mill.id,
            funding_source_id=funding_sources[5].id,  # Congressional
            status=ApplicationStatus.UNDER_REVIEW,
            application_round="FY2026",
            requested_amount=3000000,
            submission_date=date(2025, 2, 23),
            notes="Congressional appropriation request through Oregon delegation",
            documents_folder="/sites/DallasMillStation/CIP Congressional Funding"
        )
    ]
    
    db.session.add_all(applications)
    db.session.commit()
    
    # Create Time Entries
    time_entries = [
        TimeEntry(
            project_id=dallas_mill.id,
            user_name="Diana Marenco",
            description="LIHTC application development and review",
            hours=8.5,
            hourly_rate=125.0,
            date=date(2025, 6, 20),
            is_billable=True
        ),
        TimeEntry(
            project_id=dallas_mill.id,
            user_name="Diana Marenco",
            description="FHLB AHP application coordination and submission",
            hours=6.0,
            hourly_rate=125.0,
            date=date(2025, 6, 21),
            is_billable=True
        ),
        TimeEntry(
            project_id=dallas_mill.id,
            user_name="Diana Marenco",
            description="Congressional funding documentation and stakeholder coordination",
            hours=4.5,
            hourly_rate=125.0,
            date=date(2025, 6, 22),
            is_billable=True
        ),
        TimeEntry(
            project_id=sample_project.id,
            user_name="Diana Marenco",
            description="Pre-development planning and site analysis",
            hours=5.0,
            hourly_rate=125.0,
            date=date(2025, 6, 23),
            is_billable=True
        )
    ]
    
    db.session.add_all(time_entries)
    db.session.commit()
    
    print("Database seeded successfully with Dallas Mill Station and sample data!")

