import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional, Any
from datetime import datetime, date
import re
from loguru import logger


class DataValidator:
    """
    Data validation utilities for electricity consumption data
    
    Validates:
    - Data types and formats
    - Value ranges and constraints
    - Data consistency and integrity
    - Time series continuity
    - Business rule compliance
    """
    
    def __init__(self):
        self.validation_rules = {
            'meter_id': {
                'required': True,
                'type': str,
                'pattern': r'^METER_\d{6}$',
                'max_length': 50
            },
            'consumption': {
                'required': True,
                'type': (int, float),
                'min_value': 0,
                'max_value': 1000,  # Reasonable upper bound for daily consumption
                'allow_null': False
            },
            'date': {
                'required': True,
                'type': (str, date, datetime),
                'date_format': '%Y-%m-%d',
                'min_date': '2014-01-01',
                'max_date': '2030-12-31'
            },
            'customer_category': {
                'required': False,
                'type': str,
                'allowed_values': ['residential', 'commercial', 'industrial']
            }
        }
        self.validation_errors = []
        self.validation_warnings = []
    
    def validate_data_types(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Validate data types in the DataFrame
        
        Returns:
            Dictionary with validation results
        """
        try:
            logger.info("Validating data types...")
            
            results = {
                'valid': True,
                'errors': [],
                'warnings': [],
                'column_types': {}
            }
            
            for column in df.columns:
                results['column_types'][column] = str(df[column].dtype)
                
                if column in self.validation_rules:
                    rule = self.validation_rules[column]
                    expected_type = rule.get('type')
                    
                    if expected_type:
                        # Check for required columns
                        if rule.get('required', False) and column not in df.columns:
                            results['errors'].append(f"Required column '{column}' is missing")
                            results['valid'] = False
                            continue
                        
                        # Validate data types for non-null values
                        non_null_data = df[column].dropna()
                        if len(non_null_data) > 0:
                            if expected_type == str:
                                if not all(isinstance(x, str) for x in non_null_data.iloc[:100]):  # Sample check
                                    results['warnings'].append(f"Column '{column}' contains non-string values")
                            elif expected_type in [(int, float), (float, int)]:
                                if not pd.api.types.is_numeric_dtype(df[column]):
                                    results['errors'].append(f"Column '{column}' should be numeric")
                                    results['valid'] = False
            
            logger.success("Data type validation completed")
            return results
            
        except Exception as e:
            logger.error(f"Error validating data types: {e}")
            return {'valid': False, 'errors': [str(e)], 'warnings': [], 'column_types': {}}
    
    def validate_value_ranges(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Validate value ranges and constraints
        
        Returns:
            Dictionary with validation results
        """
        try:
            logger.info("Validating value ranges...")
            
            results = {
                'valid': True,
                'errors': [],
                'warnings': [],
                'range_violations': {}
            }
            
            for column in df.columns:
                if column in self.validation_rules:
                    rule = self.validation_rules[column]
                    violations = []
                    
                    # Check minimum value
                    if 'min_value' in rule and pd.api.types.is_numeric_dtype(df[column]):
                        min_violations = (df[column] < rule['min_value']).sum()
                        if min_violations > 0:
                            violations.append(f"{min_violations} values below minimum ({rule['min_value']})")
                    
                    # Check maximum value
                    if 'max_value' in rule and pd.api.types.is_numeric_dtype(df[column]):
                        max_violations = (df[column] > rule['max_value']).sum()
                        if max_violations > 0:
                            violations.append(f"{max_violations} values above maximum ({rule['max_value']})")
                    
                    # Check allowed values
                    if 'allowed_values' in rule:
                        invalid_values = ~df[column].dropna().isin(rule['allowed_values'])
                        if invalid_values.any():
                            unique_invalid = df[column].dropna()[invalid_values].unique()
                            violations.append(f"Invalid values: {list(unique_invalid)}")
                    
                    # Check string patterns
                    if 'pattern' in rule and column in df.columns:
                        pattern = re.compile(rule['pattern'])
                        non_null_values = df[column].dropna().astype(str)
                        invalid_pattern = ~non_null_values.str.match(pattern, na=False)
                        if invalid_pattern.any():
                            violations.append(f"{invalid_pattern.sum()} values don't match pattern {rule['pattern']}")
                    
                    if violations:
                        results['range_violations'][column] = violations
                        if any('values below minimum' in v or 'values above maximum' in v for v in violations):
                            results['warnings'].extend([f"{column}: {v}" for v in violations])
                        else:
                            results['errors'].extend([f"{column}: {v}" for v in violations])
                            results['valid'] = False
            
            logger.success("Value range validation completed")
            return results
            
        except Exception as e:
            logger.error(f"Error validating value ranges: {e}")
            return {'valid': False, 'errors': [str(e)], 'warnings': [], 'range_violations': {}}
    
    def validate_data_consistency(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Validate data consistency and integrity
        
        Returns:
            Dictionary with validation results
        """
        try:
            logger.info("Validating data consistency...")
            
            results = {
                'valid': True,
                'errors': [],
                'warnings': [],
                'consistency_issues': {}
            }
            
            # Check for duplicate records
            if 'meter_id' in df.columns and 'date' in df.columns:
                duplicates = df.duplicated(['meter_id', 'date']).sum()
                if duplicates > 0:
                    results['errors'].append(f"Found {duplicates} duplicate meter_id/date combinations")
                    results['valid'] = False
                    results['consistency_issues']['duplicates'] = duplicates
            
            # Check for missing required values
            for column in df.columns:
                if column in self.validation_rules:
                    rule = self.validation_rules[column]
                    if rule.get('required', False) and not rule.get('allow_null', True):
                        null_count = df[column].isnull().sum()
                        if null_count > 0:
                            results['errors'].append(f"Required column '{column}' has {null_count} null values")
                            results['valid'] = False
            
            # Check data volume per meter
            if 'meter_id' in df.columns:
                meter_counts = df['meter_id'].value_counts()
                insufficient_data = (meter_counts < 30).sum()
                if insufficient_data > 0:
                    results['warnings'].append(f"{insufficient_data} meters have less than 30 days of data")
                    results['consistency_issues']['insufficient_data_meters'] = insufficient_data
                
                # Check for extremely high data volumes (possible duplicates)
                excessive_data = (meter_counts > 2000).sum()
                if excessive_data > 0:
                    results['warnings'].append(f"{excessive_data} meters have more than 2000 records")
            
            logger.success("Data consistency validation completed")
            return results
            
        except Exception as e:
            logger.error(f"Error validating data consistency: {e}")
            return {'valid': False, 'errors': [str(e)], 'warnings': [], 'consistency_issues': {}}
    
    def validate_time_series_continuity(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Validate time series data continuity
        
        Returns:
            Dictionary with validation results
        """
        try:
            logger.info("Validating time series continuity...")
            
            results = {
                'valid': True,
                'errors': [],
                'warnings': [],
                'continuity_issues': {}
            }
            
            if 'meter_id' not in df.columns or 'date' not in df.columns:
                results['warnings'].append("Cannot validate time series continuity: missing meter_id or date columns")
                return results
            
            # Convert date column if needed
            df_temp = df.copy()
            if not pd.api.types.is_datetime64_any_dtype(df_temp['date']):
                try:
                    df_temp['date'] = pd.to_datetime(df_temp['date'])
                except Exception as e:
                    results['errors'].append(f"Cannot convert date column to datetime: {e}")
                    results['valid'] = False
                    return results
            
            # Check for date gaps per meter (optimized for large datasets)
            meters_with_gaps = 0
            total_gaps = 0
            large_gaps = 0
            
            # Sample a subset for performance with large datasets
            unique_meters = df_temp['meter_id'].unique()
            if len(unique_meters) > 1000:
                logger.info(f"Large dataset ({len(unique_meters)} meters), sampling 1000 meters for continuity check")
                sample_meters = np.random.choice(unique_meters, size=1000, replace=False)
            else:
                sample_meters = unique_meters
            
            for meter_id in sample_meters:
                meter_data = df_temp[df_temp['meter_id'] == meter_id].sort_values('date')
                if len(meter_data) > 1:
                    date_diffs = meter_data['date'].diff().dt.days
                    gaps = date_diffs[date_diffs > 1]
                    
                    if len(gaps) > 0:
                        meters_with_gaps += 1
                        total_gaps += len(gaps)
                        large_gaps += (gaps > 7).sum()  # Gaps larger than 1 week
            
            # Scale up results if we sampled
            if len(unique_meters) > 1000:
                scale_factor = len(unique_meters) / len(sample_meters)
                meters_with_gaps = int(meters_with_gaps * scale_factor)
                total_gaps = int(total_gaps * scale_factor)
                large_gaps = int(large_gaps * scale_factor)
            
            if meters_with_gaps > 0:
                results['warnings'].append(f"{meters_with_gaps} meters have date gaps")
                results['continuity_issues']['meters_with_gaps'] = meters_with_gaps
                results['continuity_issues']['total_gaps'] = total_gaps
                
                if large_gaps > 0:
                    results['warnings'].append(f"{large_gaps} large gaps (>7 days) found")
                    results['continuity_issues']['large_gaps'] = large_gaps
            
            # Check date range coverage
            date_range = df_temp['date'].max() - df_temp['date'].min()
            results['continuity_issues']['date_range_days'] = date_range.days
            
            # Check for future dates
            today = pd.Timestamp.now().date()
            future_dates = (df_temp['date'].dt.date > today).sum()
            if future_dates > 0:
                results['warnings'].append(f"{future_dates} records have future dates")
                results['continuity_issues']['future_dates'] = future_dates
            
            logger.success("Time series continuity validation completed")
            return results
            
        except Exception as e:
            logger.error(f"Error validating time series continuity: {e}")
            return {'valid': False, 'errors': [str(e)], 'warnings': [], 'continuity_issues': {}}
    
    def validate_business_rules(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Validate business-specific rules for electricity data
        
        Returns:
            Dictionary with validation results
        """
        try:
            logger.info("Validating business rules...")
            
            results = {
                'valid': True,
                'errors': [],
                'warnings': [],
                'business_rule_violations': {}
            }
            
            if 'consumption' in df.columns:
                # Rule 1: No negative consumption
                negative_consumption = (df['consumption'] < 0).sum()
                if negative_consumption > 0:
                    results['errors'].append(f"Found {negative_consumption} records with negative consumption")
                    results['valid'] = False
                    results['business_rule_violations']['negative_consumption'] = negative_consumption
                
                # Rule 2: Check for unrealistic consumption values
                consumption_stats = df['consumption'].describe()
                
                # Extremely high consumption (> 99.9th percentile * 3)
                high_threshold = df['consumption'].quantile(0.999) * 3
                extreme_high = (df['consumption'] > high_threshold).sum()
                if extreme_high > 0:
                    results['warnings'].append(f"{extreme_high} records with extremely high consumption (>{high_threshold:.2f})")
                    results['business_rule_violations']['extreme_high_consumption'] = extreme_high
                
                # Too many zero consumption days per meter
                if 'meter_id' in df.columns:
                    zero_consumption_by_meter = df[df['consumption'] == 0].groupby('meter_id').size()
                    problematic_meters = (zero_consumption_by_meter > 100).sum()  # More than 100 zero days
                    if problematic_meters > 0:
                        results['warnings'].append(f"{problematic_meters} meters have >100 zero consumption days")
                        results['business_rule_violations']['problematic_zero_meters'] = problematic_meters
                
                # Rule 3: Check consumption consistency within meters
                if 'meter_id' in df.columns:
                    meters_with_issues = 0
                    for meter_id in df['meter_id'].unique():
                        meter_data = df[df['meter_id'] == meter_id]['consumption']
                        if len(meter_data) > 10:
                            # Check for constant consumption (possible meter malfunction)
                            if meter_data.std() == 0 and meter_data.iloc[0] > 0:
                                meters_with_issues += 1
                    
                    if meters_with_issues > 0:
                        results['warnings'].append(f"{meters_with_issues} meters have constant non-zero consumption")
                        results['business_rule_violations']['constant_consumption_meters'] = meters_with_issues
            
            # Rule 4: Validate customer categories
            if 'customer_category' in df.columns:
                valid_categories = ['residential', 'commercial', 'industrial']
                invalid_categories = ~df['customer_category'].dropna().isin(valid_categories)
                if invalid_categories.any():
                    invalid_count = invalid_categories.sum()
                    results['errors'].append(f"{invalid_count} records have invalid customer categories")
                    results['valid'] = False
            
            logger.success("Business rules validation completed")
            return results
            
        except Exception as e:
            logger.error(f"Error validating business rules: {e}")
            return {'valid': False, 'errors': [str(e)], 'warnings': [], 'business_rule_violations': {}}
    
    def comprehensive_validation(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Run comprehensive validation on the dataset
        
        Returns:
            Complete validation report
        """
        try:
            logger.info("Starting comprehensive data validation...")
            
            # Run all validation checks
            type_validation = self.validate_data_types(df)
            range_validation = self.validate_value_ranges(df)
            consistency_validation = self.validate_data_consistency(df)
            continuity_validation = self.validate_time_series_continuity(df)
            business_validation = self.validate_business_rules(df)
            
            # Combine all results
            comprehensive_report = {
                'dataset_info': {
                    'total_records': len(df),
                    'total_columns': len(df.columns),
                    'columns': list(df.columns),
                    'memory_usage_mb': df.memory_usage(deep=True).sum() / 1024 / 1024
                },
                'overall_validity': (
                    type_validation['valid'] and 
                    range_validation['valid'] and 
                    consistency_validation['valid'] and 
                    continuity_validation['valid'] and 
                    business_validation['valid']
                ),
                'validation_results': {
                    'data_types': type_validation,
                    'value_ranges': range_validation,
                    'data_consistency': consistency_validation,
                    'time_series_continuity': continuity_validation,
                    'business_rules': business_validation
                },
                'summary': {
                    'total_errors': (
                        len(type_validation['errors']) + 
                        len(range_validation['errors']) + 
                        len(consistency_validation['errors']) + 
                        len(continuity_validation['errors']) + 
                        len(business_validation['errors'])
                    ),
                    'total_warnings': (
                        len(type_validation['warnings']) + 
                        len(range_validation['warnings']) + 
                        len(consistency_validation['warnings']) + 
                        len(continuity_validation['warnings']) + 
                        len(business_validation['warnings'])
                    )
                }
            }
            
            # Calculate validation score (0-100)
            total_checks = 20  # Approximate number of validation checks
            validation_score = max(0, 100 - (comprehensive_report['summary']['total_errors'] * 10) - 
                                 (comprehensive_report['summary']['total_warnings'] * 2))
            comprehensive_report['validation_score'] = min(100, validation_score)
            
            logger.success(f"Comprehensive validation completed. Score: {validation_score}/100")
            
            return comprehensive_report
            
        except Exception as e:
            logger.error(f"Error in comprehensive validation: {e}")
            return {
                'overall_validity': False,
                'validation_results': {},
                'summary': {'total_errors': 1, 'total_warnings': 0},
                'validation_score': 0,
                'error': str(e)
            }


# Utility functions
def validate_electricity_data(df: pd.DataFrame) -> Dict[str, Any]:
    """Convenience function for validating electricity data"""
    validator = DataValidator()
    return validator.comprehensive_validation(df)


def quick_data_check(df: pd.DataFrame) -> bool:
    """Quick validation check - returns True if data passes basic validation"""
    try:
        validator = DataValidator()
        type_check = validator.validate_data_types(df)
        consistency_check = validator.validate_data_consistency(df)
        return type_check['valid'] and consistency_check['valid']
    except:
        return False