<template>
  <div class="about">
    <top-bar title="Some Help!"></top-bar>
    <v-container>
          <v-card>
          <v-tabs vertical>
            <v-tab>
              About
            </v-tab>
            <v-tab>
              Container Types
            </v-tab>
            <v-tab>
              Permissions/Access Control  
            </v-tab>
            <v-tab>
              API
            </v-tab>
            <v-tab-item>
              <v-card flat>
                <v-card-subtitle>
                  <h3>This is Hinkskalle!</h3>
                </v-card-subtitle>
                <v-card-text>
                  <p>Hinkskalle started out as a Singularity container registry compatible with the library 
                    protocol (similar to <a href="https://cloud.sylabs.io/">the Sylabs Cloud</a>), but expanded
                    into a general purpose registry supporting the 
                    <a href="https://github.com/opencontainers/distribution-spec">OCI distribution</a> 
                    protocol (docker, podman, ORAS) and arbitrary data.</p>
                </v-card-text>
              </v-card>
              <v-card>
                <v-card-subtitle>
                  <h3>Library Structure</h3>
                </v-card-subtitle>
                <v-card-text>
                  <p>A Library path looks like this: <code>/entity/collection/container:tag</code></p>
                  <h4>Entity</h4>
                  <p>This is the basic (root) element. You are an entity called <code>username</code>,
                  e.g. <code>test.hase</code>. You can do whatever you like underneath that!</p>
                  <p>We also have a special entity <code>default</code> with some general purpose 
                  containers and data.</p>
                  <h4>Collection</h4>
                  <p>You can group/organize your containers and data into collections. It's up to
                    you how that looks. As an inspiration: This might be by type (docker, singularity, ...)
                    or by project or by purpose.</p>
                  <h4>Container</h4>
                  <p>Now we're getting there. These hold the data.</p>
                </v-card-text>
              </v-card>
            </v-tab-item>
            <v-tab-item>
              You can have containers and stuff.
            </v-tab-item>
            <v-tab-item>
              Yes yes.
            </v-tab-item>
            <v-tab-item>
              Over there.
            </v-tab-item>
          </v-tabs>
          </v-card>
    </v-container>
  </div>
</template>

<script lang="ts">
import Vue from 'vue';

export default Vue.extend({
  name: 'About',
});
</script>