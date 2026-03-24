def main() -> None:
    print(
        "Use `celery -A crawler.celery_app:celery worker -l info -Q crawl` "
        "or `make crawler run` to start the crawler worker."
    )


if __name__ == "__main__":
    main()
