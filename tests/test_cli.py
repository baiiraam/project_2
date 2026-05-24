'''CLI test functions.'''

class TestCLIMainFunction:
    """Tests for main function CLI dispatch."""

    def test_main_analyze_subcommand(self, mocker):
        """Test main with analyze subcommand."""
        # Mock setup_logging to prevent output noise
        mocker.patch("src.cli.main.setup_logging")

        # Mock parse_args to return an object with command='analyze' and image_path
        mock_args = mocker.MagicMock()
        mock_args.command = "analyze"
        mock_args.image_path = "test_image.jpg"
        # Ensure no 'func' attribute exists (since analyze doesn't use it)
        # Don't set func attribute at all
        if hasattr(mock_args, 'func'):
            delattr(mock_args, 'func')

        mock_parse_args = mocker.patch("argparse.ArgumentParser.parse_args")
        mock_parse_args.return_value = mock_args

        mock_analyze = mocker.patch("src.cli.main.analyze_command")

        from src.cli.main import main
        main()

        mock_analyze.assert_called_once_with("test_image.jpg")

    def test_main_get_subcommand(self, mocker):
        """Test main with get subcommand."""
        mocker.patch("src.cli.main.setup_logging")

        mock_args = mocker.MagicMock()
        mock_args.command = "get"
        mock_args.id = 42
        if hasattr(mock_args, 'func'):
            delattr(mock_args, 'func')

        mock_parse_args = mocker.patch("argparse.ArgumentParser.parse_args")
        mock_parse_args.return_value = mock_args

        mock_get = mocker.patch("src.cli.main.get_command")

        from src.cli.main import main
        main()

        mock_get.assert_called_once_with(42)

    def test_main_list_subcommand(self, mocker):
        """Test main with list subcommand."""
        mocker.patch("src.cli.main.setup_logging")

        mock_args = mocker.MagicMock()
        mock_args.command = "list"
        if hasattr(mock_args, 'func'):
            delattr(mock_args, 'func')

        mock_parse_args = mocker.patch("argparse.ArgumentParser.parse_args")
        mock_parse_args.return_value = mock_args

        mock_list = mocker.patch("src.cli.main.list_command")

        from src.cli.main import main
        main()

        mock_list.assert_called_once()

    def test_main_list_with_limit(self, mocker):
        """Test main list subcommand with limit argument."""
        mocker.patch("src.cli.main.setup_logging")

        mock_args = mocker.MagicMock()
        mock_args.command = "list"
        mock_args.limit = 20  # This will be ignored by main()
        if hasattr(mock_args, 'func'):
            delattr(mock_args, 'func')

        mock_parse_args = mocker.patch("argparse.ArgumentParser.parse_args")
        mock_parse_args.return_value = mock_args

        mock_list = mocker.patch("src.cli.main.list_command")

        from src.cli.main import main
        main()

        # list_command doesn't accept limit parameter in main()
        mock_list.assert_called_once()
