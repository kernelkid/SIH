def format_pagination_response(paginated_data, items_data):
    return {
        "pagination": {
            "page": paginated_data.page,
            "per_page": paginated_data.per_page,
            "total": paginated_data.total,
            "pages": paginated_data.pages,
            "has_next": paginated_data.has_next,
            "has_prev": paginated_data.has_prev
        },
        "items": items_data
    }