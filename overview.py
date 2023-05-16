from pathlib import Path
import json
from datetime import datetime


def get_branch(version_number: str):
    if version_number == "SNAPSHOT":
        return "master"

    return "openwrt-" + version_number.rsplit(".", maxsplit=1)[0]


def update_index(versions: list):
    html_index = Path("index.tmpl.html").read_text()
    html_archive = Path("archive.tmpl.html").read_text()
    archived_releases = ""

    stable = versions[1]["version_number"]
    stable_branch = versions[1]["branch"]

    oldstable = None
    for version in versions[2:]:
        if not oldstable and version["branch"] != stable_branch:
            oldstable = version["version_number"]
        else:
            archived_releases += f"""        <li>
          <a href="//archive.openwrt.org/releases/{version['version_number']}/targets/"
            >OpenWrt {version['version_number']}</a
          >
        </li>"""


    html_index = html_index.replace("{{stable}}", stable).replace("{{oldstable}}", oldstable)
    html_archive = html_archive.replace("{{archived_releases}}", archived_releases)

    Path("index.html").write_text(html_index)
    Path("archive.html").write_text(html_archive)


def update_versions(path: Path):
    versions = []

    for overview_path in path.rglob("overview.json"):
        overview_obj = json.loads(overview_path.read_text())
        print(overview_path)
        versions.append(
            {
                "version_number": overview_obj["version_number"],
                "version_code": overview_obj["version_code"],
                "path": str(overview_path.parent.relative_to(path)),
                "branch": get_branch(overview_obj["version_number"]),
            }
        )

    versions.sort(key=lambda x: x["version_code"], reverse=True)
    print(json.dumps(versions, indent=2))
    (path / "versions.json").write_text(json.dumps(versions, indent=2))

    update_index(versions)


def update_overview(path: Path):
    print(path)
    overview = {
        "profiles": [],
    }

    for profiles_path in path.rglob("profiles.json"):
        metadata_obj = json.loads(profiles_path.read_text())
        profiles_obj = metadata_obj.pop("profiles")
        build_at = datetime.utcfromtimestamp(int(metadata_obj["source_date_epoch"]))

        if not "version_number" in overview:
            overview["version_number"] = metadata_obj["version_number"]
            overview["version_code"] = metadata_obj["version_code"]

        profiles_folder = path / "targets" / metadata_obj["target"] / "profiles"
        profiles_folder.mkdir(parents=True, exist_ok=True)
        existing_profiles = set(profiles_folder.glob("*.json"))

        for profile_id, profile_obj in profiles_obj.items():
            overview["profiles"].append(
                {
                    "target": metadata_obj["target"],
                    "titles": profile_obj["titles"],
                    "id": profile_id,
                }
            )
            (profiles_folder / f"{profile_id}.json").write_text(
                json.dumps(
                    {
                        **metadata_obj,
                        **profile_obj,
                        "id": profile_id,
                        "build_at": str(build_at),
                    },
                    indent=2,
                )
            )

            existing_profiles.discard(profiles_folder / f"{profile_id}.json")

        for profile_path in existing_profiles:
            profile_path.unlink()

    if overview["profiles"]:
        overview["profiles"].sort(key=lambda x: x["id"])
        (path / "overview.json").write_text(json.dumps(overview, indent=2))


if __name__ == "__main__":
    # for version in Path().cwd().rglob("targets"):
    #     update_overview(version.parent)
    update_versions(Path("tmp/downloads.openwrt.org/"))
