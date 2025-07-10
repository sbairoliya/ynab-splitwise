"""Tests for configuration and authentication."""

import os
import pytest
from unittest.mock import patch

from src.ynab_splitwise.auth.config import Config
from src.ynab_splitwise.utils.exceptions import AuthenticationError, ConfigurationError


class TestConfig:
    """Test configuration management."""
    
    def test_config_initialization_success(self):
        """Test successful configuration initialization."""
        with patch.dict(os.environ, {
            'SPLITWISE_API_KEY': 'test_api_key_12345',
            'YNAB_ACCESS_TOKEN': 'test_token_67890'
        }):
            config = Config()
            assert config.splitwise_api_key == 'test_api_key_12345'
            assert config.ynab_access_token == 'test_token_67890'
            assert config.ynab_account_name == 'Splitwise (Wallet)'
            assert config.ynab_api_url == 'https://api.ynab.com/v1'
            assert config.splitwise_api_url == 'https://secure.splitwise.com/api/v3.0'
    
    def test_config_missing_splitwise_api_key(self):
        """Test configuration fails when Splitwise API key is missing."""
        with patch.dict(os.environ, {'YNAB_ACCESS_TOKEN': 'test_token'}, clear=True):
            with pytest.raises(ConfigurationError) as exc_info:
                Config()
            assert "SPLITWISE_API_KEY" in str(exc_info.value)
    
    def test_config_missing_ynab_access_token(self):
        """Test configuration fails when YNAB access token is missing."""
        with patch.dict(os.environ, {'SPLITWISE_API_KEY': 'test_api_key'}, clear=True):
            with pytest.raises(ConfigurationError) as exc_info:
                Config()
            assert "YNAB_ACCESS_TOKEN" in str(exc_info.value)
    
    def test_config_custom_account_name(self):
        """Test configuration with custom account name."""
        with patch.dict(os.environ, {
            'SPLITWISE_API_KEY': 'test_api_key',
            'YNAB_ACCESS_TOKEN': 'test_token',
            'YNAB_ACCOUNT_NAME': 'My Custom Account'
        }):
            config = Config()
            assert config.ynab_account_name == 'My Custom Account'
    
    def test_validate_success(self):
        """Test successful validation."""
        with patch.dict(os.environ, {
            'SPLITWISE_API_KEY': 'valid_api_key_123456789',
            'YNAB_ACCESS_TOKEN': 'valid_token_987654321'
        }):
            config = Config()
            # Should not raise any exception
            config.validate()
    
    def test_validate_invalid_api_key(self):
        """Test validation fails with invalid API key."""
        with patch.dict(os.environ, {
            'SPLITWISE_API_KEY': 'short',
            'YNAB_ACCESS_TOKEN': 'valid_token_987654321'
        }):
            config = Config()
            with pytest.raises(AuthenticationError) as exc_info:
                config.validate()
            assert "Invalid Splitwise API key" in str(exc_info.value)
    
    def test_validate_invalid_access_token(self):
        """Test validation fails with invalid access token."""
        with patch.dict(os.environ, {
            'SPLITWISE_API_KEY': 'valid_api_key_123456789',
            'YNAB_ACCESS_TOKEN': 'short'
        }):
            config = Config()
            with pytest.raises(AuthenticationError) as exc_info:
                config.validate()
            assert "Invalid YNAB access token" in str(exc_info.value)
    
    def test_validate_empty_account_name(self):
        """Test validation fails with empty account name."""
        with patch.dict(os.environ, {
            'SPLITWISE_API_KEY': 'valid_api_key_123456789',
            'YNAB_ACCESS_TOKEN': 'valid_token_987654321',
            'YNAB_ACCOUNT_NAME': '   '
        }):
            config = Config()
            with pytest.raises(ConfigurationError) as exc_info:
                config.validate()
            assert "Invalid YNAB account name" in str(exc_info.value)
    
    def test_get_splitwise_headers(self):
        """Test Splitwise headers generation."""
        with patch.dict(os.environ, {
            'SPLITWISE_API_KEY': 'test_api_key',
            'YNAB_ACCESS_TOKEN': 'test_token'
        }):
            config = Config()
            headers = config.get_splitwise_headers()
            
            assert headers['Authorization'] == 'Bearer test_api_key'
            assert headers['Content-Type'] == 'application/json'
            assert headers['Accept'] == 'application/json'
    
    def test_get_ynab_config(self):
        """Test YNAB configuration generation."""
        with patch.dict(os.environ, {
            'SPLITWISE_API_KEY': 'test_api_key',
            'YNAB_ACCESS_TOKEN': 'test_token'
        }):
            config = Config()
            ynab_config = config.get_ynab_config()
            
            assert ynab_config['access_token'] == 'test_token'
            assert ynab_config['host'] == 'https://api.ynab.com/v1'