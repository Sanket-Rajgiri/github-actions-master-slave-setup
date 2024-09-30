const https = require("https");

async function getBody(options) {
  // Return new promise
  console.log("started getbody function");
  return new Promise(function (resolve, reject) {
    const request = https.request(options.url, options, function (response) {
      let data = "";

      response.on("data", (chunk) => {
        data += chunk;
      });

      response.on("end", () => {
        if (data.length > 0) {
          var res = JSON.parse(data);
          console.log(res);
          resolve(res);
        } else {
          resolve(null);
        }
      });
    });

    request.on("error", (e) => {
      reject(e);
    });

    request.end();
  });
}

async function removeRunner(repo, instanceId) {
  const owner = process.env.Owner;
  const password = process.env.PersonalAccessToken;
  const auth =
    "Bearer " + Buffer.from(owner + ":" + password).toString("base64");
  const result = await getBody({
    method: "GET",
    url: `https://api.github.com/repos/${owner}/${repo}/actions/runners`,
    headers: {
      Accept: "application/vnd.github+json",
      Authorization: auth,
      "X-GitHub-Api-Version": "2022-11-28",
      "User-Agent": owner,
    },
  });
  console.log(
    `Removing GitHub self-hosted running from EC2 instance ${instanceId}`
  );

  console.log(result, Array.isArray(result.runners));
  const off_runners = result.runners.find((r) => r.name === instanceId); //[1]
  console.log(off_runners, Array.isArray(off_runners));
  if (off_runners) {
    await getBody({
      method: "DELETE",
      url: `https://api.github.com/repos/${owner}/${repo}/actions/runners/${off_runners.id}`,
      headers: {
        Accept: "application/vnd.github+json",
        Authorization: auth,
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": owner,
      },
    });
    console.log(
      `GitHub self-hosted running from EC2 instance ${instanceId} removed for repo ${repo} `
    );
  } else {
    console.log(
      `No GitHub self-hosted running for EC2 instance ${instanceId} skip for repo ${repo}`
    );
  }
}

exports.handler = async (event) => {
  const repo = process.env.Repository;
  console.log(JSON.stringify(event));
  if (event["detail-type"] !== "EC2 Instance Terminate Successful") {
    return {
      statusCode: 200,
      body: `no action for event type ${event["detail-type"]}`,
    };
  }
  const instanceId = event.detail.EC2InstanceId;
  await removeRunner("iitb-portal-frontend", instanceId);
  await removeRunner("iitb-portal-backend", instanceId);
};
